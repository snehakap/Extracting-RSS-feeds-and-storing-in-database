import feedparser
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Define the SQLite database engine
engine = create_engine('sqlite:///news_articles.db', echo=True)

# Define the base class for declarative class definitions
Base = declarative_base()

# Define the Article and Source classes
class Article(Base):
    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(String)
    published_date = Column(DateTime, default=datetime.utcnow)
    source_id = Column(Integer, ForeignKey('sources.id'))

    source = relationship('Source', back_populates='articles')

class Source(Base):
    __tablename__ = 'sources'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String)

    articles = relationship('Article', back_populates='source')

# Create the tables in the database
Base.metadata.create_all(engine)

# Create a session to interact with the database
Session = sessionmaker(bind=engine)
session = Session()

def parse_feeds(feeds):
    articles = []
    for feed_url in feeds:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            article = {}
            article['title'] = entry.title
            article['content'] = entry.get('summary', '')
            article['publish'] = entry.get('published', '')
            article['source_url'] = entry.link
            if article not in articles:
                articles.append(article)
    return articles

def store_articles(articles):
    for article in articles:
        existing_article = session.query(Article).filter(Article.title == article['title']).first()
        if existing_article:
            print(f"Article '{article['title']}' already exists in the database.")
        else:
            source = session.query(Source).filter(Source.url == article['source_url']).first()
            if not source:
                source = Source(name='Unknown', url=article['source_url'])
                session.add(source)
                session.commit()

            published_date = None
            if article['publish']:
                try:
                    published_date = datetime.strptime(article['publish'], '%a, %d %b %Y %H:%M:%S')
                except ValueError:
                    print(f"Error parsing date for article '{article['title']}'")

            new_article = Article(
                title=article['title'],
                content=article['content'],
                published_date=published_date,
                source_id=source.id
            )
            session.add(new_article)
            session.commit()
            print(f"Article '{article['title']}' added to the database.")

# List of RSS feeds
rss_feeds = [
    "http://rss.cnn.com/rss/cnn_topstories.rss",
    "http://qz.com/feed",
    "http://feeds.foxnews.com/foxnews/politics",
    "http://feeds.reuters.com/reuters/businessNews",
    "http://feeds.feedburner.com/NewshourWorld",
    "https://feeds.bbci.co.uk/news/world/asia/india/rss.xml"
]

# Parse the feeds and store articles in the database
parsed_articles = parse_feeds(rss_feeds)
store_articles(parsed_articles)
