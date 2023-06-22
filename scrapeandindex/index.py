import os
import psycopg2
import pinecone
from datetime import datetime
import json
from densevectors import get_dense_vector
from sparsevectors import get_sparse_vector

#  get DATABASE_URL environment variable
DATABASE_URL = os.environ['DATABASE_URL']
PINECONE_API_KEY = os.environ['PINECONE_API_KEY']
PINECONE_ENV = os.environ['PINECONE_ENV']
PINECONE_INDEX_NAME = os.environ['PINECONE_INDEX_NAME']
VERIFIED_DOMAIN = os.environ['VERIFIED_DOMAIN']

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

# select the next heading with compiledtext = ''
cur.execute("SELECT rowid, indexed, compiledtext FROM headings")
headings = cur.fetchall()

i = 0
for heading in headings:

    print(i)

    if heading[1] == True:
        continue

    texttoembed = str(heading[2])

    if texttoembed == '':
        # set indexed to True
        cur.execute("UPDATE headings SET indexed = %s WHERE rowid = %s", (True, heading[0]))
        conn.commit()
        continue

    # get the dense vector
    densevector = get_dense_vector(texttoembed)

    # get the sparse vector
    sparsevector = get_sparse_vector(texttoembed)

    # index the vector
    upsert_response = index.upsert(
        vectors=[
            {'id': f'{heading[0]}',
             'values': densevector,
             'sparse_values': sparsevector,}
        ],
        namespace = 'langchaindocs'
    )

    # set indexed to True
    cur.execute("UPDATE headings SET indexed = %s WHERE rowid = %s", (True, heading[0]))
    conn.commit()

    print(upsert_response)
    i+=1

# close the cursor
cur.close()

# close the connection
conn.close()