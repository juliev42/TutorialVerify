## Overall Functionality

1. User asks to either verify or create course materials
2. Verify mode: 
    - Ask user for document to verify against database
    - Call to GPT3.5 to extract the specific parts of the document that could be potentially out of date
    - Search pinecone DB to get the most relevant related info from the database, checking against the most recent updates
    - Call to GPT3.5 to check the extracted sections against the retreived documents