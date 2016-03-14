from pymongo import MongoClient
import logging,re,time
from secrets import *
import requests
import textblob
import langid
import collections

client = MongoClient()
db = client.fb
pagesCollection = db.pages
postsCollection = db.posts
commentsCollection = db.comments
likesCollection=db.likes

###################
# Parameters
###################

LIMIT=1000
# Page limit
postsLimit=100
# Hard limit from API=250

nSkip=5
# Hit API for query nSkip times
# before skipping

nWait=60
# Wait between API errors

postSleepTime=0.3
pageSleepTime=8
# Pause so API not thrashed

####################
# DB helper functions
####################

def addTimestampToPage(id):
    '''
    Adds current timestamp to page
    '''
    pagesCollection.update({'id':id},{'$set':{'checked':[int(time.time())]}})

def updatePageTimestamp(id):
    '''
    Updates timestamp of page
    '''
    pagesCollection.update({'id':id},{'$addToSet':{'checked':int(time.time())}})

def isPostInDb(id):
    '''
    Tests if a post is in post collection
    Returns Bool
    '''
    nMatches=postsCollection.find({'id':id}).count()
    if nMatches==0:
        return False
    elif nMatches==1:
        return True
    else:
#        logging.warning('Duplicate post %s' % id)
        return True

def isPageInDb(id):
    '''
    Tests if a page is in pages collection
    Returns Bool
    '''
    nMatches=pagesCollection.find({'id':id}).count()

    if nMatches==0:
        return False
    elif nMatches==1:
        return True
    else:
#        logging.warning('Duplicate page %s' % id)
        return True

def countCollections():
    print '%d pages' % pagesCollection.count()
    print '%d posts' % postsCollection.count()
    print '%d comments' % commentsCollection.count()
    print '%d likes' % likesCollection.count()

def addCommentsToDb(commentsData):
    nAdded=nAlready=0
    for comment in commentsData['data']:
        if not isCommentInDb(comment['id']):
            commentsCollection.insert_one(comment)
            nAdded+=1
        else:
            nAlready+=1
    logging.warning('%d comments added (%d already in DB)' % (nAdded,nAlready))

def addPageToDb(page):
    pagesCollection.insert_one(page)

def addLikesToDb(likes):
    nAdded=nAlready=0
    for like in likes['data']:
        if not isLikeInDb(like['id']):
            likesCollection.insert_one(like)
            nAdded+=1
        else:
            nAlready+=1
    logging.warning('%d likes added (%d already in DB)' % (nAdded,nAlready))

def addPostToDb(post):
    print 'Adding posts'
    postsCollection.insert_one(post)

def isLikeInDb(id):
    '''
    Tests if a like is in comments collection
    Returns Bool
    '''
    nMatches=likesCollection.find({'id':id}).count()
    if nMatches==0:
        return False
    elif nMatches==1:
        return True
    else:
        logging.warning('Duplicate like %s' % id)
        return True

def isCommentInDb(id):
    '''
    Tests if a comment is in comments collection
    Returns Bool
    '''
    nMatches=commentsCollection.find({'id':id}).count()
    if nMatches==0:
        return False
    elif nMatches==1:
        return True
    else:
#        logging.warning('Duplicate comment %s' % id)
        return True

####################
# Other functions
####################

def clean(s):
    if s:
        s=re.sub(',|;|:|"|\'|\?|\(|\)|\n|\t|\-|\=|\+',' ',s.lower())
        return s.strip()
    else:
        return None


def handleResult(statusCode,returnText):
    '''
    Parses API call result to determine if successful
    or to wait or abandon
    Returns success,skip (both Bool)
    '''
    if statusCode==200:
        # OK
        return True,False

    if statusCode in [102,10,463,467]:
        # Access token expired
        logging.warning('API error: %d %s' % (statusCode,returnText))
        return False,True
    elif statusCode in [2,4,17,341,500]:
        # Wait and retry
        logging.warning('API error - waiting: %d %s' % (statusCode,returnText))
        return False,False
    elif statusCode in [506,1609005]:
        # Skip
        logging.warning('API error - skipping: %d %s' % (statusCode,returnText))
        return False,True
    elif statusCode in [400]:
        # Skip
        logging.warning('API error,page migrated? - skipping: %d %s' % (statusCode,returnText))
        return False,True
    else:
        logging.warning('API error - unknown code %d %s' % (statusCode,returnText))
        return False, True


###################################################
def getPostsFromPage(pageId,raw=False,limit=100,since=None,until=None):
###################################################
    '''
    Requests list of posts, list of comments and
    list of likes from a page
    Returns a list of JSON objects
    or if raw=True, a string description of posts(deprecated)
    Actually does adding of comments and likes
    '''

    logging.info('Getting posts,comments,likes for page %s' % pageId)

    tempUrl='https://graph.facebook.com/%s/posts?&limit=%d&access_token=%s' % (pageId,postsLimit,ACCESSTOKEN)
    # since=2011-07-01&until=2012-08-08&

    if since and until:
        tempUrl+='&since=%s&until%s' % (since,until)
        logging.info('....between %s and %s' % (since,until))

    out=[]
    outFull=[]

    comments=None
    likes=None

    r=requests.get(tempUrl)
    ######################################################
    success=None
    nAttempts=0

    while not success:
        # Keep looping if unsuccessful
        r=requests.get(tempUrl)
        success,skip=handleResult(r.status_code,r.text)
        # Try, find out if successful or should skip

        if skip or nAttempts==nSkip:
            # If tried nSkip times or if should skip
            r={'data':[],'paging':None}
            if nAttempts==nSkip:
                logging.warning('Skipping posts after %d attempts' % nAttempts)
                return ([],[],[])
        time.sleep(nWait)
        nAttempts+=1
    ######################################################

    for n,d in enumerate(r.json()['data']):

        time.sleep(postSleepTime)

        name=d.get('name')
        id=d.get('id')
        print 'Post %d %s %s' % (n,name,id)

        message=d.get('message')
        if message:
            message=clean(message)
        else:
            logging.warning('No message for post %s' % d['id'])

        description=d.get('description')
        if description:
            description=clean(description)
        else:
            logging.warning('No description for post %s' % d['id'])

        caption=d.get('caption')
        if caption:
            caption=clean(caption)
        else:
            logging.warning('No caption for post %s' % d['id'])

        d['page_id']=pageId
        d['retrieved']=time.time()

        if d.get('icon'):del d['icon']
        if d.get('picture'):del d['picture']
        if d.get('privacy'):del d['privacy']
        # Don't need these

        try:
            shareCount=d['shares']['count']
            d['shares']=shareCount
        except:
            pass
        # Simplify this

        if message:
#            print message
            out.append(message)
            if not langid.classify(message)[0]=='en':
                try:
                    enMessage=textblob.TextBlob(message).translate().string
                    enMessage=clean(enMessage)
                    out.append('==>'+enMessage+'---------')
                    d['en_message']=enMessage
                except:
                    logging.warning('Translation failed')
                    enMessage=None
        if description:
            out.append(description)
            if not langid.classify(description)[0]=='en':
                try:
                    enDescription=textblob.TextBlob(description).translate().string
                    enDescription=clean(enDescription)
                    out.append('==>'+enDescription+'---------')
                    d['en_description']=enDescription
                except:
                    logging.warning('Translation failed')
                    enDescription=None
        if caption:
            out.append(caption)
            if not langid.classify(caption)[0]=='en':
                try:
                    enCaption=textblob.TextBlob(caption).translate().string
                    enCaption=clean(enCaption)
                    out.append('==>'+enCaption+'---------')
                    d['en_caption']=enCaption
                except:
                    enCaption=None

        try:
            comments=d['comments']
            del d['comments']
        except:
            comments=None

        if comments:
            logging.info('Getting comments...')
            commentData=getComments(comments,pageId)
            # This does all the paging
#            for c in commentData['data']:
#                print 'Comments data:',c.keys()
#                print 'Likes:',c[u'user_likes'],c.get('likes')
            addCommentsToDb(commentData)

            # TODO get comment likes

        try:
            likes=d['likes']
            del d['likes']
        except:
            likes=None

        if False:
            if likes:
                logging.info('Getting likes...')
                likeData=getLikes(likes,pageId,id)
                # This does all the paging
                addLikesToDb(likeData)
        else:
            print 'Skipping likes'


        outFull.append(d)

    if raw:
        '\n'.join(out)
        pass # return string
    else:
        return outFull,comments,likes

##################################
def getNextLikes(nextToken):
##################################
    '''
    Given a paging token for next page of likes returns the raw data
    '''
#    logging.warning('Getting next likes: %s' % nextToken)
    res=requests.get(nextToken)

    if not res.status_code==200:
        logging.warning('Error with next likes data %d %s' % (res.status_code,res.text))
        return None
    else:
        return res.json()

##################################
def getNextComments(nextToken):
##################################
    '''
    Given a paging token for next page of likes returns the raw data
    '''
    res=requests.get(nextToken)

    if not res.status_code==200:
        logging.warning('Error with next comments data %d' % res.status_code)
        return None
    else:
        return res.json()

##################################
def getComments(comments,pageId):
##################################
    '''
    Takes a dictionary of comment data from API with keys
    [paging,data]. If paging information is present, keep
    requesting pages
    '''

    if comments.get('paging'):

        current=comments

        while current['paging'].get('next'):
            logging.info('Paging comments...')
            current=getNextComments(current['paging']['next'])
            comments['data'].extend(current['data'])

            if not current.get('paging'):
                break
    return comments

####################################
def getLikes(likes,pageId,id):
####################################
    '''
    Takes a dictionary of like data from API with keys
    [paging,data], pageId and post id. If paging information is present, keep
    requesting pages
    '''


    if likes.get('paging'):
        current=likes
        #print '>>>',likes.keys()
        #print '>>>',current.keys()
        while current['paging'].get('next'):
            logging.info('Paging likes... %s' % current['paging']['next'])
            current=getNextLikes(current['paging']['next'])
            if current:
                print 'Got next page of likes (current) (%d so far)' % len(likes['data'])
                likes['data'].extend(current['data'])
            else:
                break
            # TODO better error handling

        print 'Got %d likes after paging' % len(likes['data'])
#    print 'Likes type %s' % type(likes)
#    print likes.keys()

    for like in likes['data']:
        like['id']='%s_%s' % (id,like['id'])
        # Make a unique like ID made up of post id_likeid
        like['parent_id']=id
        # Keep parent id of comment/post for getting most liked content

#    print 'Likes',likes.keys()
#    print likes.get('paging')
#    print likes['data'][0]
    return likes
