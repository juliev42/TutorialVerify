## Overall Functionality

1. User asks to either verify or create course materials
2. Verify mode: 
    - Ask user for document to verify against database
    - Call to GPT3.5 to extract the specific parts of the document that could be potentially out of date
    - Search pinecone DB to get the most relevant related info from the database, checking against the most recent updates
    - Call to GPT3.5 to check the extracted sections against the retreived documents
3. Creation mode: 
    - Ask user for the course syllabus areas they would like to have content generated in 
    - Search pinecone DB to get the most relevant related info from the database, checking against the most recent updates
    - Call GPT3.5 to synthesize a syllabus with the pinecone DB and relevant info 
    - Prompt to see if the user requires additional information