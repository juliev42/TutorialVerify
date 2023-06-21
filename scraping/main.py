import os
import psycopg2
from scraper import *

#  get DATABASE_URL environment variable
DATABASE_URL = os.environ['DATABASE_URL']

conn = psycopg2.connect(DATABASE_URL)

# LANGCHAIN scraping logic

# close the connection
conn.close()