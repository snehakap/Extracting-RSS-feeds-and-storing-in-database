
# Import necessary modules
import feedparser
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from datetime import datetime
import uuid
from celery import Celery
import spacy
import csv

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
    category = Column(String, default='Others')  # Added for category

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

# Configure Celery
# Configure Celery
app = Celery('tasks', broker='redis://:hc4vtkIYNrbiKZJwPsIXVpnGBRBi1G0K@redis-16182.c1.asia-northeast1-1.gce.cloud.redislabs.com:16182', backend='redis://:hc4vtkIYNrbiKZJwPsIXVpnGBRBi1G0K@redis-16182.c1.asia-northeast1-1.gce.cloud.redislabs.com:16182')

# Load spaCy English language model
nlp = spacy.load("en_core_web_sm")

# Define Celery task for category classification
@app.task
def classify_category(article_id, parsed_articles):
    article = session.query(Article).filter(Article.id == article_id).first()
    if article:
        doc = nlp(article.content)
        categories = []

        # Classify the article based on certain keywords or patterns
        for token in doc:
            if token.text.lower() in ["terrorism", "protest", "political unrest", "riot"]:
                categories.append("Terrorism/Protest/Political Unrest/Riot")
            elif token.text.lower() in ["positive", "uplifting"]:
                categories.append("Positive/Uplifting")
            elif token.text.lower() in ["natural", "disaster"]:
                categories.append("Natural Disasters")

        # If no specific category is found, assign it to "Others"
        if not categories:
            categories.append("Others")

        article.category = ', '.join(categories)
        session.commit()

        # Update the category in the parsed_articles dictionary
        for parsed_article in parsed_articles:
            if parsed_article['id'] == article_id:
                parsed_article['category'] = article.category

        return parsed_articles  # Return the updated parsed_articles dictionary

# Define function to parse feeds and send articles to the Celery queue
def parse_feeds(feeds):
    articles = []
    for feed_url in feeds:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            article = {}
            article['id'] = str(uuid.uuid4())  # Generate unique ID
            article['title'] = entry.title
            article['content'] = entry.get('summary', '')
            article['publish'] = entry.get('published', '')
            article['source_url'] = entry.link
            if article not in articles:
                articles.append(article)
                # Send article to Celery queue for further processing
                articles = classify_category.delay(article['id'], articles).get()  # Get the updated parsed_articles
    return articles

# Define function to export data to CSV
def export_to_csv(articles):
    with open('classified_articles.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'title', 'content', 'published_date', 'source_url', 'category', 'publish']  # Include 'publish'
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for article in articles:
            writer.writerow(article)

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

# Export classified articles to CSV
export_to_csv(parsed_articles)






# Import necessary modules
import feedparser
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from datetime import datetime
import uuid
from celery import Celery
import spacy
import csv

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
    category = Column(String, default='Others')  # Added for category

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

# Configure Celery
app = Celery('tasks', broker='redis://:hc4vtkIYNrbiKZJwPsIXVpnGBRBi1G0K@redis-16182.c1.asia-northeast1-1.gce.cloud.redislabs.com:16182')

# Load spaCy English language model
nlp = spacy.load("en_core_web_sm")

# Define Celery task for category classification
@app.task
def classify_category(article_id, parsed_articles):
    article = session.query(Article).filter(Article.id == article_id).first()
    if article:
        doc = nlp(article.content)
        categories = []

        # Classify the article based on certain keywords or patterns
        for token in doc:
            if token.text.lower() in ["terrorism", "protest", "political unrest", "riot"]:
                categories.append("Terrorism/Protest/Political Unrest/Riot")
            elif token.text.lower() in ["positive", "uplifting"]:
                categories.append("Positive/Uplifting")
            elif token.text.lower() in ["natural", "disaster"]:
                categories.append("Natural Disasters")

        # If no specific category is found, assign it to "Others"
        if not categories:
            categories.append("Others")

        article.category = ', '.join(categories)
        session.commit()

        # Update the category in the parsed_articles dictionary
        for parsed_article in parsed_articles:
            if parsed_article['id'] == article_id:
                parsed_article['category'] = article.category

        return parsed_articles  # Return the updated parsed_articles dictionary

# Define function to parse feeds and send articles to the Celery queue
def parse_feeds(feeds):
    articles = []
    for feed_url in feeds:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            article = {}
            article['id'] = str(uuid.uuid4())  # Generate unique ID
            article['title'] = entry.title
            article['content'] = entry.get('summary', '')
            article['publish'] = entry.get('published', '')
            article['source_url'] = entry.link
            if article not in articles:
                articles.append(article)
                # Send article to Celery queue for further processing
                classify_category.delay(article['id'])  # Pass article id
    return articles

# Define function to export data to CSV
def export_to_csv(articles):
    with open('classified_articles.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'title', 'content', 'source_url', 'publish', 'category'] 
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for article in articles:
            writer.writerow(article)

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

# Export classified articles to CSV
export_to_csv(parsed_articles)




import feedparser
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
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
