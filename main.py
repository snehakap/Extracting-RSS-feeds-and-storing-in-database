import feedparser 
rss_feeds = ["http://rss.cnn.com/rss/cnn_topstories.rss",
             "http://qz.com/feed",
             "http://feeds.foxnews.com/foxnews/politics",
             "http://feeds.reuters.com/reuters/businessNews",
             "http://feeds.feedburner.com/NewshourWorld",
             "https://feeds.bbci.co.uk/news/world/asia/india/rss.xml"]
def parse_feeds(feeds):
  articles = []
  for feed_url in feeds:
    feed = feedparser.parse(feed_url)
    for i in feed.entries:
      article = {}
      article['title'] = i.title
      article['content'] = i.get('summary',' ')
      article['publish'] = i.get('published',' ')
      article['source_url'] = i.link
#To check for duplicate articles
      if article not in articles:
        articles.append(article)  
    return articles
