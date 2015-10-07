### Summary
Notebook and script to query Facebook API and write results to MongoDB. Steps are as follows

1. Define keywords to grab pages (matches description and/or title)  
2. Grabs pages and associated meta-data  
3. Grabs latest posts; limited to ~250 and recent time range  
4. Pages through all comments and likes on each post  

### Dependencies

* [Requests](http://docs.python-requests.org/en/latest/)  For robust HTTP requests
* [Langid](https://pypi.python.org/pypi/langid)  For detecting non-English content
* [TextBlob](http://textblob.readthedocs.org/en/dev/)  Abstraction for Google translating non-English content
* [MongoDB connector](http://api.mongodb.org/python/current/)  To easily write results to DB in JSON format
* [Facebook API key](https://developers.facebook.com/docs/graph-api/overview/#step2)  For API authentication
