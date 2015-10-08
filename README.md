### Summary
Notebook and script to query Facebook API and write results to MongoDB. Steps are as follows

1. Define keywords to grab pages (matches description and/or title)  
2. Grabs pages and associated meta-data  
3. Grabs latest posts; limited to ~250 and recent time range  
4. Pages through all comments and likes on each post  

### Logic
The high-level flow of the script is as follows:

1. Keywords to find pages are defined  
2. A call to the API returns all page IDs matching these keywords  
3. A second call gets the full information for these pages  
4. Another API call gets the latest posts on these pages  
5. Two separate calls are made to get the likes and the comments on each post

At each point, the data returned is tested to see if it already exists in the DB (according to a unique ID) and if not is added, if so is ignored

### MongoDB Structure  

Requires a MongoDB with four collections  

1. Pages  
2. Posts  
3. Comments  
4. Likes  

### Dependencies

* [Requests](http://docs.python-requests.org/en/latest/)  For robust HTTP requests
* [Langid](https://pypi.python.org/pypi/langid)  For detecting non-English content
* [TextBlob](http://textblob.readthedocs.org/en/dev/)  Abstraction for Google translating non-English content
* [MongoDB connector](http://api.mongodb.org/python/current/)  To easily write results to DB in JSON format
* [Facebook API key](https://developers.facebook.com/docs/graph-api/overview/#step2)  For API authentication
