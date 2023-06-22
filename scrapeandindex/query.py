import psycopg2
import os

DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(DATABASE_URL)



def select_row_by_index(index, tablename, columnname):
    with conn.cursor() as cur:
        cur.execute(f"SELECT {columnname} FROM {tablename} LIMIT 1 OFFSET %s", (index,))
        row = cur.fetchone()
        return row
    
# get the heading in the 5th row of the headings table
heading = select_row_by_index(500, 'headings', '*')
print(heading)

# get the url at the urlid in the headings table
url = select_row_by_index(heading[0], 'urls', '*')
print(url)

def get_url_from_heading_idx(heading_idx):
    heading = select_row_by_index(heading_idx, 'headings', 'urlid')
    url = select_row_by_index(heading[0], 'urls', '*')
    return url # list of items related to the url

def get_heading_by_rowid(rowid):
    with conn.cursor() as cur:

        cur.execute("SELECT * FROM headings WHERE rowid = %s", (rowid,))
        heading = cur.fetchone()
        return heading # list of items related to the heading