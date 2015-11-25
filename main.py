# -*- coding: utf-8 -*-
#
#  Copyright (c) 2014 Will Adams (izilly)
#  Distributed under the terms of the Modified BSD License.
#  The full license is in the file LICENSE, distributed with this software.


import sys
from urlparse import parse_qsl
import xbmcgui
import xbmcplugin
import xbmcaddon
from xml.etree.ElementTree import ElementTree as et
import urllib2

#from pudb.remote import set_trace
#set_trace(term_size=(140, 40))

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])

FEED_URLS = {'hardcore_history': 'http://feeds.feedburner.com/dancarlin/history?format=xml',
             'common_sense': 'http://feeds.feedburner.com/dancarlin/commonsense?format=xml',
            }
FEED_ICONS = {'hardcore_history': 'http://www.dancarlin.com/wp-content/uploads/2014/08/hh-cover.jpg',
              'common_sense': 'http://www.dancarlin.com/wp-content/uploads/2014/08/cs-cover.jpg',
             }
FEED_GENRES = {'hardcore_history': 'History',
               'common_sense': 'News'
              }

FEED_NAMES = {'hardcore_history': xbmcaddon.Addon().getLocalizedString(30001).encode('utf-8'),
              'common_sense': xbmcaddon.Addon().getLocalizedString(30002).encode('utf-8'),
             }


def get_categories():
    """
    Get a list of categories (podcasts).
    
    Returns:
        list of categories
    """
    return ['hardcore_history', 'common_sense']

def get_episodes(category):
    """
    Get a list of episodes in a given category.

    Returns:
        list of episodes
    """
    feed_url = FEED_URLS[category]
    xmlfile = urllib2.urlopen(feed_url)
    tree = et(file=xmlfile)
    root = tree.getroot()
    channel = root[0]
    items = channel.findall('item')
    episodes = [get_episode_info(i, category) for i in items]
    return episodes

def get_episode_info(episode, category):
    """
    Get information on a single episode.

    Returns:
        dict of episode info
    """
    ei = {}
    ei['title'] = episode.find('title').text
    ei['description'] = episode.find('description').text
    ei['date'] = episode.find('pubDate').text
    enclosure = episode.find('enclosure')
    ei['length'] = enclosure.get('length')
    ei['url'] = enclosure.get('url')
    ei['thumb'] = FEED_ICONS[category]
    ei['genre'] = FEED_GENRES[category]
    return ei

def list_categories():
    """
    Create the list of categories in the Kodi interface.

    Returns:
        None
    """
    categories = get_categories()
    listing = []
    for category in categories:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=FEED_NAMES[category], thumbnailImage=FEED_ICONS[category])
        # set fanart
        list_item.setProperty('fanart_image', FEED_ICONS[category])

        # Set additional info for the list item.
        list_item.setInfo('video', {'title': category, 'genre': 'news'})
        list_item.setInfo('audio', {'title': category, 'genre': 'news'})
        # Create a URL for the plugin recursive callback.
        # e.g., plugin://plugin.audio.dancarlin/?action=listing&category=common_sense
        url = '{0}?action=listing&category={1}'.format(_url, category)
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the listing as a 3-element tuple.
        listing.append((url, list_item, is_folder))
    # Add our listing to Kodi.
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def list_episodes(category):
    """
    Create the list of playable items in Kodi interface.

    Args:
        category: podcast/category (str)

    Returns:
        None
    """
    episodes = get_episodes(category)
    listing = []
    for episode in episodes:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=episode['title'], thumbnailImage=episode['thumb'])
        # set fanart
        list_item.setProperty('fanart_image', episode['thumb'])
        # Set additional info for the list item.
        #list_item.setInfo('video', {'title': episode['title'], 
                                    #'genre': episode['genre'],
                                    #'plot': episode['description'],
                                    #'plotoutline': episode['description'],
                                   #})
        list_item.setInfo('music', {'title': episode['title'], 
                                    'album': episode['title'],
                                    'comment': episode['description'],
                                    'artist': 'Dan Carlin',
                                    'genre': episode['genre'],
                                   })
        # Set additional graphics (banner, poster, landscape etc.) for the list item.
        list_item.setArt({'landscape': episode['thumb']})
        # Set 'IsPlayable' property to 'true'.
        # This is mandatory for playable items!
        list_item.setProperty('IsPlayable', 'true')
        # Create a URL for the plugin recursive callback.
        # e.g., plugin://plugin.video.dancarlin/?action=play&episode=http://media.url
        url = '{0}?action=play&episode={1}'.format(_url, episode['url'])
        # Add the list item to a virtual Kodi folder.
        # is_folder = False means that this item won't open any sub-list.
        is_folder = False
        # Add our item to the listing as a 3-element tuple.
        listing.append((url, list_item, is_folder))
    # Add our listing to Kodi.
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def play_episode(path):
    """
    Play an episode with the given path.

    Args:
        path: Kodi url of episode (str)

    Returns:
        None
    """
    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=path)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)

def router(paramstring):
    """
    Call the appropriate function for the given paramstring.

    Args:
        paramstring: query string passed to the add-on

    Returns:
        None
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
        if params.get('content_type') and len(params) == 1:
            list_categories()
        elif params['action'] == 'listing':
            # Display the list of episodes in a given category.
            list_episodes(params['category'])
        elif params['action'] == 'play':
            # Play episode from a provided URL.
            play_episode(params['episode'])
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of categories
        list_categories()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])

