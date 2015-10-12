from pymongo import MongoClient
import logging,re,time
client = MongoClient()
db = client.fb
pagesCollection = db.pages
postsCollection = db.posts
commentsCollection = db.comments
likesCollection=db.likes

####################
# DB functions
####################

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
    