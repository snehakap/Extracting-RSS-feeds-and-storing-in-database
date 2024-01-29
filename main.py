import feedparser
import logging
import csv
import uuid
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from datetime import datetime
from celery import Celery
import spacy

# Configure logging
logging.basicConfig(filename='news_classification.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

# Set up logging
logger = logging.getLogger(__name__)

@app.task
def classify_category(article_id):
    try:
        article = session.query(Article).filter(Article.id == article_id).first()
        if article:
            doc = nlp(article.content)
            categories = []

            # Check for specific keywords and entities
            keywords = {
                "terrorism", "protest", "political unrest", "riot",
                "positive", "uplifting",
                "natural", "disaster"
            }

            entities = {ent.text.lower() for ent in doc.ents}

            # Extract relevant tokens and their POS tags
            relevant_tokens = [(token.text.lower(), token.pos_) for token in doc if token.text.lower() in keywords]

            # Classify the article based on the context of the text
            if any(entity in entities for entity in ["terrorism", "protest", "political unrest", "riot"]) \
                    or any(token[0] in {"terrorism", "protest", "political unrest", "riot"} for token in relevant_tokens):
                categories.append("Terrorism/Protest/Political Unrest/Riot")
            elif any(entity in entities for entity in ["positive", "uplifting"]) \
                    or any(token[0] in {"positive", "uplifting"} for token in relevant_tokens):
                categories.append("Positive/Uplifting")
            elif any(entity in entities for entity in ["natural", "disaster"]) \
                    or any(token[0] in {"natural", "disaster"} for token in relevant_tokens):
                categories.append("Natural Disasters")
            else:
                categories.append("Others")

            article.category = ', '.join(categories)
            session.commit()
    except Exception as e:
        logger.error(f"Error occurred while classifying category for article ID {article_id}: {e}")

# Define function to parse feeds and send articles to the Celery queue
def parse_feeds(feeds):
    articles = []
    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                article = {}
                article['id'] = str(uuid.uuid4())
                article['title'] = entry.title
                article['content'] = entry.get('summary', '')
                article['publish'] = entry.get('published', '')
                article['source_url'] = entry.link

                # Fetch category for the article
                doc = nlp(article['content'])
                categories = []
                for token in doc:
                    if token.text.lower() in ["terrorism", "protest", "political unrest", "riot"]:
                        categories.append("Terrorism/Protest/Political Unrest/Riot")
                    elif token.text.lower() in ["positive", "uplifting"]:
                        categories.append("Positive/Uplifting")
                    elif token.text.lower() in ["natural", "disaster"]:
                        categories.append("Natural Disasters")
                if not categories:
                    categories.append("Others")
                article['category'] = ', '.join(categories)

                if article not in articles:
                    articles.append(article)
                    # Send article to Celery queue for further processing
                    classify_category.delay(article['id'])  # Pass article id
        except Exception as e:
            logger.error(f"Error occurred while parsing feed {feed_url}: {e}")
    return articles

# Define function to export data to CSV
def export_to_csv(articles):
    try:
        with open('classified_articles.csv', 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['id', 'title', 'content', 'source_url', 'publish', 'category']  
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for article in articles:
                writer.writerow(article)
    except Exception as e:
        logger.error(f"Error occurred while exporting articles to CSV: {e}")

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
