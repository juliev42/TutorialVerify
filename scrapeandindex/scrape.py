import os
import psycopg2
from traverse import *
import pinecone
from datetime import datetime

#  get DATABASE_URL environment variable
DATABASE_URL = os.environ['DATABASE_URL']
PINECONE_API_KEY = os.environ['PINECONE_API_KEY']
PINECONE_ENV = os.environ['PINECONE_ENV']
PINECONE_INDEX_NAME = os.environ['PINECONE_INDEX_NAME']
VERIFIED_DOMAIN = os.environ['VERIFIED_DOMAIN']

def url_in_database(url, cur):
    """
    Checks if the url is already in the database
    """
    cur.execute("SELECT * FROM urlstoscrape WHERE url = %s", (url,))
    return cur.fetchone() is not None

# connect to postgres
conn = psycopg2.connect(DATABASE_URL)

# create a cursor
cur = conn.cursor()

# if table urls does not exist, create it. The columns that it contains are url, a boolean named verified, and a timestamp named timestamp
cur.execute("CREATE TABLE IF NOT EXISTS urls (url text, verified boolean, timestamp timestamp)")

# if table headings does not exist, create it. The columns that it contains are urlid, headingtext, listofsubheadingids, and listofparagraphids, indexed defaults to false
cur.execute("CREATE TABLE IF NOT EXISTS headings (urlid text, headingtext text, listofsubheadingids text, listofparagraphids text, indexed boolean)")

# commit the changes
conn.commit()

# if table paragraphs does not exist, create it. The columns that it contains are paragraphtext
cur.execute("CREATE TABLE IF NOT EXISTS paragraphs (paragraphtext text)")

# commit the changes
conn.commit()

# if table urls to scrape doesn't exist, create it. The columns that it contains are url, scraped
cur.execute("CREATE TABLE IF NOT EXISTS urlstoscrape (url text, scraped boolean)")

# commit the changes
conn.commit()

# LANGCHAIN scraping logic

# ask for user input for the initial url
url = input("Enter the initial url: ")

# if the url entered is not empty and the url is not already in the database, add it to the database
if url != "" and not url_in_database(url, cur):
    cur.execute("INSERT INTO urlstoscrape (url, scraped) VALUES (%s, %s)", (url, False))
    conn.commit()

# get the next heading id to be added to the headings table, get the length of the headings table
cur.execute("SELECT COUNT(*) FROM headings")
headingidnext = cur.fetchone()[0]

# get the next paragraph id to be added to the paragraphs table, get the length of the paragraphs table
cur.execute("SELECT COUNT(*) FROM paragraphs")
paragraphidnext = cur.fetchone()[0]

# while there are still urls to scrape
i = 0
while True:

    print('number of urls scraped :', i)

    # get the next url to scrape
    cur.execute("SELECT * FROM urlstoscrape WHERE scraped = %s", (False,))

    if cur.fetchone() is None:
        break
    else:
        cur.execute("SELECT * FROM urlstoscrape WHERE scraped = %s", (False,))
        url = cur.fetchone()[0]

    # scrape the url
    urls, data = scrape_url(url)

    if len(urls) == 0:
        # mark the url as scraped
        cur.execute("UPDATE urlstoscrape SET scraped = %s WHERE url = %s", (True, url))
        conn.commit()
        continue

    # get timestamp
    timestamp = datetime.now()

    # get the id of the url
    cur.execute("SELECT COUNT(*) FROM urls")
    urlid = cur.fetchone()[0]

    headdom = data[1]
    paradom = data[2]

    if len(headdom) == 0 or len(paradom) == 0:
        # mark the url as scraped
        cur.execute("UPDATE urlstoscrape SET scraped = %s WHERE url = %s", (True, url))
        conn.commit()
        continue

    print('url is scraped')

    # if url is a page in the VERIFIED_DOMAIN, add it to the urls table and mark it as verified, VERIFIED_DOMAIN is of the form example.com
    # TODO: this can be optimized
    if VERIFIED_DOMAIN in url:
        cur.execute("INSERT INTO urls (url, verified, timestamp) VALUES (%s, %s, %s)", (url, True, timestamp))
        conn.commit()
    else:
        cur.execute("INSERT INTO urls (url, verified, timestamp) VALUES (%s, %s, %s)", (url, False, timestamp))
        conn.commit()

    # tread with care, RECURSION AHEAD!!!
    def call_related_headings(headingid, headings, listofrelatedids=None, nextheading=False):

        if listofrelatedids is None:
            listofrelatedids = []

        if not nextheading:
            if headings[headingid][3]!=None:
                subheadingid = headings[headingid][3]
                listofrelatedids.append(subheadingid)
                listofrelatedids = call_related_headings(subheadingid, headings, listofrelatedids, True)

        if nextheading:
            if headings[headingid][4]!=None:
                nextheadingid = headings[headingid][4]
                listofrelatedids.append(nextheadingid)
                listofrelatedids = call_related_headings(nextheadingid, headings, listofrelatedids, True)

        return listofrelatedids

    for headingid_ in range(len(headdom)): # heading is a list of the form [something, something, headingtext, subheadingid, nextheadingid, list of paragraph ids]

        heading_ = headdom[headingid_]

        nextheadingsitem = []
        nextheadingsitem.append(urlid)
        nextheadingsitem.append(heading_[2])
        listofsubheadingids = call_related_headings(headingid_, headdom)
        nextheadingsitem.append(listofsubheadingids)
        nextheadingsitem.append(heading_[5])
        nextheadingsitem.append(False)

        # add the heading to the database, but before that, add headingidnext+1 to each of the subheadingids, and paragraphidnext+1 to each of the paragraphids
        nextheadingsitem[2] = [headingidnext+1+x for x in nextheadingsitem[2]]
        nextheadingsitem[3] = [paragraphidnext+1+x for x in nextheadingsitem[3]]

        # add the heading to the database
        cur.execute("INSERT INTO headings (urlid, headingtext, listofsubheadingids, listofparagraphids, indexed) VALUES (%s, %s, %s, %s, %s)", (nextheadingsitem[0], nextheadingsitem[1], nextheadingsitem[2], nextheadingsitem[3], nextheadingsitem[4]))
        conn.commit()
    
    print('headings are added to the database')

    # increment the headingidnext
    headingidnext += len(headdom)

    for paragraphid_ in range(len(paradom)): # paragraph is a list of the form [something, something, paragraphtext, something]

        paragraph_ = paradom[paragraphid_]

        nextparagraphitem = []
        nextparagraphitem.append(paragraph_[2])

        # add the paragraph to the database
        cur.execute("INSERT INTO paragraphs (paragraphtext) VALUES (%s)", (nextparagraphitem[0],))
        conn.commit()

    print('paragraphs are added to the database')

    # increment the paragraphidnext
    paragraphidnext += len(paradom)

    # mark the url as scraped
    cur.execute("UPDATE urlstoscrape SET scraped = %s WHERE url = %s", (True, url))

    # commit the changes
    conn.commit()

    # add the urls to the urlstoscrape table if it is a VERIFIED_DOMAIN and if it is not already in the urlstoscrape table
    for url_ in urls:
        if VERIFIED_DOMAIN in url_[1] and not url_in_database(url_[1], cur):
            cur.execute("INSERT INTO urlstoscrape (url, scraped) VALUES (%s, %s)", (url_[1], False))
            conn.commit()
    
    print("scraped url : ", url)
    i+=1

# add the column compiledtext to the headings table and update the information

# modify the compiledtext column in headings
i = 0

# select the next heading with compiledtext = ''
cur.execute("SELECT rowid, headingtext, listofparagraphids, compiledtext FROM headings")
headings = cur.fetchall()

def select_row_by_index(index):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM paragraphs LIMIT 1 OFFSET %s", (index - 1,))
        row = cur.fetchone()
        return row

for heading in headings:

    # print(heading)
    # input()

    print(i)

    # if heading[-1] != '':
    #     print(heading, 'already has compiledtext')
    #     continue

    # initialise compiledtext
    compiledtext = ''

    # get the heading text
    compiledtext += heading[1]

    # load the list of paragraph ids
    # heading[3] is a string representation of a list of paragraph ids, but it is enclosed in {}, so we remove the first and last characters and then load it as a list
    listofparagraphids = json.loads('['+heading[2][1:-1]+']')

    # get the paragraph texts
    for paragraphid in listofparagraphids:
        paragraph = select_row_by_index(paragraphid)
        if paragraph is not None:
            # print(paragraph)
            # input('wait:')
            compiledtext += ' '
            compiledtext += paragraph[0]

    # remove double or more spaces with single spaces
    compiledtext = ' '.join([word for word in compiledtext.split(' ') if word != ''])

    print('compiledtext: ', compiledtext)
    # update the compiledtext column
    cur.execute("UPDATE headings SET compiledtext = %s WHERE rowid = %s", (compiledtext, heading[0]))

    # save
    conn.commit()
    i += 1

# close the cursor
cur.close()
# terminate the driver
driver.quit()
# close the connection
conn.close()