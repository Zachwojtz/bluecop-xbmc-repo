import xbmc
import xbmcgui
import xbmcplugin
import urllib
import urllib2
import httplib
import sys
import os
import re

from BeautifulSoup import BeautifulSoup
from BeautifulSoup import BeautifulStoneSoup
import resources.lib._common as common
from pyamf import remoting

pluginhandle=int(sys.argv[1])

BASE_URL = 'http://www.fxnetworks.com/episodes.php'
BASE = 'http://www.fxnetworks.com'

def masterlist():
    rootlist()

def rootlist():
    data = common.getURL(BASE_URL)
    tree=BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
    menu=tree.find('ul', attrs={'class':'shows'}).findAll('li',recursive=False)
    for item in menu:
        try:
            url = item.find(attrs={'class':'action watch-episodes'})['href']
            url = url.replace('/fod/play.php?sh=','/fod/').replace('/watch/','/fod/')   
            thumb = item.find('img')['src']
            showname = item.find(attrs={'class':'content'})('h2')[0].string
            common.addDirectory(showname, 'fx', 'show', url, thumb)
            print url
        except:
            print 'no watch episode action'

def show(url=common.args.url):
    common.addDirectory('Full Episodes', 'fx', 'episodes', url+'/rss.xml')
    common.addDirectory('Clips & Extras', 'fx', 'episodes', url+'/rss_bc_videoextras.xml')


def episodes(url=common.args.url):
    data = common.getURL(url)
    tree=BeautifulStoneSoup(data, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
    showname = tree.find('channel').find('title').string
    menu=tree.findAll('item')
    for item in menu:
        print item.prettify()
        name = item('title')[0].string
        url = item('link')[0].string.split('/')[-1]
        description = item('description')[0].string
        try:
            thumb = item('thumbnail')[0].string
        except:
            thumb = item('media:thumbnail')[0]['url']
        u = sys.argv[0]
        u += '?url="'+urllib.quote_plus(url)+'"'
        u += '&mode="fx"'
        u += '&sitemode="play"'
        item=xbmcgui.ListItem(name, iconImage=thumb, thumbnailImage=thumb)
        item.setInfo( type="Video", infoLabels={ "Title":name,
                                                 #"Season":season,
                                                 #"Episode":episode,
                                                 "Plot":description,
                                                 #"premiered":airDate,
                                                 #"Duration":duration,
                                                 "TVShowTitle":showname
                                                 })
        item.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(pluginhandle,url=u,listitem=item,isFolder=False)

def play():
    videoPlayer = int(common.args.url)
    const = 'cd687d9fa9f678adbdccc61fe50233e43e61164e'
    playerID = 640594657001
    publisherID = 67398584001
    rtmpdata = get_clip_info(const, playerID, videoPlayer, publisherID)['renditions']
    hbitrate = -1
    for item in rtmpdata:
        bitrate = int(item['encodingRate'])
        if bitrate > hbitrate:
            hbitrate = bitrate
            urldata = item['defaultURL']
            auth = urldata.split('?')[1]
            urldata = urldata.split('&')
            rtmp = urldata[0]+'?'+auth
            playpath = urldata[1].split('?')[0]+'?'+auth
    swfUrl = 'http://admin.brightcove.com/viewer/us1.25.03.01.2011-05-12131832/federatedVideo/BrightcovePlayer.swf'
    rtmpurl = rtmp+' playpath='+playpath + " swfurl=" + swfUrl + " swfvfy=true"
    item = xbmcgui.ListItem(path=rtmpurl)
    xbmcplugin.setResolvedUrl(pluginhandle, True, item)
       
def build_amf_request(const, playerID, videoPlayer, publisherID):
    env = remoting.Envelope(amfVersion=3)
    env.bodies.append(
        (
            "/1", 
            remoting.Request(
                target="com.brightcove.player.runtime.PlayerMediaFacade.findMediaById", 
                body=[const, playerID, videoPlayer, publisherID],
                envelope=env
            )
        )
    )
    return env

def get_clip_info(const, playerID, videoPlayer, publisherID):
    conn = httplib.HTTPConnection("c.brightcove.com")
    envelope = build_amf_request(const, playerID, videoPlayer, publisherID)
    conn.request("POST", "/services/messagebroker/amf?playerKey=AQ~~,AAAAD7FExsE~,dWW_A2fca-0o0T8SJiLGfd39phbKu16R", str(remoting.encode(envelope).read()), {'content-type': 'application/x-amf'})
    response = conn.getresponse().read()
    response = remoting.decode(response).bodies[0][1].body
    return response  

