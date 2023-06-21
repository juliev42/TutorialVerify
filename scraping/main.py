import os
import psycopg2
from scraper import *
import pinecone

#  get DATABASE_URL environment variable
DATABASE_URL = os.environ['DATABASE_URL']
PINECONE_API_KEY = os.environ['PINECONE_API_KEY']
PINECONE_ENV = os.environ['PINECONE_ENV']
PINECONE_INDEX_NAME = os.environ['PINECONE_INDEX_NAME']

# connect to pinecone
pinecone.init(
    api_key=PINECONE_API_KEY,
    environment=PINECONE_ENV
)

# connect to pinecone index
index = pinecone.Index(PINECONE_INDEX_NAME)

# connect to postgres
conn = psycopg2.connect(DATABASE_URL)

# create a cursor
cur = conn.cursor()

# if table data does not exist, create it. The columns that it contains are url, text, 

# LANGCHAIN scraping logic

# close the connection
conn.close()