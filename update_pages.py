
# coding: utf-8

# In[1]:

import requests,re
import sys
sys.path.append('/usr/local/lib/python2.7/dist-packages/')
import textblob
import langid,traceback
import logging
import pandas as pd
import collections
import pymongo,time,argparse
from dateutil import parser
from secrets import *

ACCESSTOKEN=ACCESSTOKEN2
# Hack

argParser = argparse.ArgumentParser(description='Grab FB pages from MongoDB, get the least recently updated ones and grab new posts, pages, likes and comments. Optionally in a date range')


force=False

timeRange=False
since=None
until=None

db='fb'
argParser.add_argument("--db", help="Choose a DB to grab pages from",type=str,choices=['unicef','sv','fb'])

argParser.add_argument("--force", help="Turn of DB checking",action='store_true')

argParser.add_argument("--timeRange", help="Specify a time range for posts to grab/update",type=str,nargs=2)

args=argParser.parse_args()
db=args.db
'''
if '--timeRange' in sys.argv:
    timeRange=True

    i=sys.argv.index('--timeRange')

    since=sys.argv[i+1]
    until=sys.argv[i+2]

    since=parser.parse(since)
    until=parser.parse(until)

    print 'Got time range %s - %s' % (since,until)

assert db in ['unicef','sv','fb']

if timeRange:
    assert (since and until)
'''

since,until=args.timeRange

if since and until:
    timeRange=True
    since,until=parser.parse(since),parser.parse(until)

print args
print timeRange

if not force:

    answer=raw_input('Update %s DB?' % db)
    if answer.lower().strip() in ['y','yes']:
        print 'OK'
    else:
        print 'Exiting'
        sys.exit(1)

if db=='fb':
    from utils import *
elif db=='sv':
    from utils_sv import *
elif db=='unicef':
    from utils_unicef import *
else:
    print 'DB error'
    sys.exit(1)

logging.basicConfig(level=logging.INFO,
                    filename='log.log', # log to this file
                    format='%(asctime)s %(message)s') # include timestamp

#########################
def run(cur,since=None,until=None):
#########################
    for page in cur:

        #print page
        #sys.exit(1)

        if page.get('id'):

            print page['id'],page['retrieved']
            try:
            # HACK
                posts,comments,likes=getPostsFromPage(page['id'],limit=postsLimit,raw=False,since=since,until=until)
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

##############################
cur=pagesCollection.find({'checked':{'$exists':False},'relevant':{'$ne':False}},no_cursor_timeout=True)
# Get all pages that have yet to be checked

cur=pagesCollection.find({'relevant':{'$ne':False}},no_cursor_timeout=True).sort('checked.-1',1)

print since,until,timeRange

if timeRange and since and until:
    times=pd.date_range(since,until,freq='1d')
    print times

    for s,u in zip(times[::2],times[1::2]):
        logging.warning('Getting posts in range %s - %s',s,u)
        run(cur,s,u)
else:
    run(cur)
