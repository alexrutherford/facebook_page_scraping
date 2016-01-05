
# coding: utf-8

# In[1]:

import requests,re
import sys
sys.path.append('/usr/local/lib/python2.7/dist-packages/')
import textblob
import langid,traceback
import logging
import collections
import pymongo,time
from secrets import *
from utils import *


# In[3]:

#hdlr = logging.FileHandler('log.log')
#formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
#hdlr.setFormatter(formatter)

logging.basicConfig(level=logging.INFO,
                    filename='log.log', # log to this file
                    format='%(asctime)s %(message)s') # include timestamp


# In[4]:

cur=pagesCollection.find({'checked':{'$exists':False},'relevant':{'$ne':False}})
cur=pagesCollection.find({'relevant':{'$ne':False}}).sort('checked.-1',1)
# Get all pages that have yet to be checked
# Change this next to be pages sorted by last time checked

print cur.count()

for page in cur:

    #print page
    #sys.exit(1)

    if page.get('id'):

        print page['id'],page['retrieved']
        try:
        # HACK
            posts,comments,likes=getPostsFromPage(page['id'],limit=postsLimit,raw=False)
            # Get posts,comments,likes from that page

            nAdded=nAlready=0

            for post in posts:
                if not isPostInDb(post['id']):
                    addPostToDb(post)
                    nAdded+=1
                else:
                    #logging.warning('Post %s already in DB' % post['id'])
                    nAlready+=1
            logging.warning('%d posts added (%d already in DB)' % (nAdded,nAlready))
        except:
            print '***Page error'
            print traceback.print_exc()
        #addTimestampToPage(page['id'])
        updatePageTimestamp(page['id'])
        print 'Sleeping for %d' % pageSleepTime
        time.sleep(pageSleepTime)
    else:
        logging.warning('Missing page id %s' % page)


# In[ ]:

'''
/home/turing/facebook_api/utils.pyc in getLikes(likes, pageId, id)
    399         current=likes
    400
--> 401         while current['paging'].get('next'):
    402             logging.info('Paging likes... %s' % current['paging']['next'])
    403             current=getNextLikes(current['paging']['next'])

KeyError: 'paging'
'''
