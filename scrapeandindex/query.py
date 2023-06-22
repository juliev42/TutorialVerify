import psycopg2

# connect to the database
# conn = psycopg2.connect(DATABASE_URL)

# create a cursor
# cur = conn.cursor()

def select_row_by_index(index, tablename, columnname, conn):
    with conn.cursor() as cur:
        cur.execute(f"SELECT {columnname} FROM {tablename} LIMIT 1 OFFSET %s", (index,))
        row = cur.fetchone()
        return row
    
# get the heading in the 5th row of the headings table
# heading = select_row_by_index(500, 'headings', '*')
# print(heading)

# get the url at the urlid in the headings table
# url = select_row_by_index(heading[0], 'urls', '*')
# print(url)

def get_url_by_headingid(rowid, cur):
    heading = cur.execute("SELECT urlid FROM headings WHERE rowid = %s", (rowid,))
    url = select_row_by_index(heading[0], 'urls', '*')
    return url # list of items related to the url

def get_heading_by_rowid(rowid, cur): # row id is the same as pineconeid here
    cur.execute("SELECT * FROM headings WHERE rowid = %s", (rowid,))
    heading = cur.fetchone()
    return heading # list of items related to the heading

# print(get_heading_by_rowid(500))

# close the cursor
# cur.close()

# close the connection
# conn.close()