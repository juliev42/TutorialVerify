import pinecone
import openai
import os

import langchain
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.embeddings.openai import OpenAIEmbeddings


from langchain.vectorstores import Pinecone

openai_api_key = os.getenv('OPENAI_API_KEY')
pinecone_api_key = os.getenv('PINECONE_API_KEY')

class LangChainPineconeClient:
    def __init__(self, pinecone_key = pinecone_api_key, openai_key = openai_api_key, index_name):
        ## Initialize with Pinecone API key and OpenAI API key, plus relevant index name
        pinecone.init(api_key=pinecone_key, environment='us-west4-gcp-free')
        openai.api_key = openai_key

        index = pinecone.Index(index_name)
        text_field = "text"

        embed = OpenAIEmbeddings(
            model='text-embedding-ada-002',
            openai_api_key=openai_api_key
        )


        self.vectorstore = Pinecone(
            index, embed.embed_query, text_field
        )

        self.llm = ChatOpenAI(
            openai_api_key=openai_api_key,
            model_name='gpt-3.5-turbo',
            temperature=0.0)
        
        self.qa =  RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever()
        )


    def view_indexes(self):
        ## View all indexes
        return pinecone.list_indexes()
    
    def get_relevant_text(input, topic = "LangChain"):
        ## Get relevant text from input_text
        prompt = f'Extract text relevant to {topic} from the following document ' + input
        response = self.llm.run(prompt)
        return response
    
    def get_relevant_pinecone_data(self, input):
        qa_response = self.qa.run(input)
        return qa_response
    
    def ask_with_context(self, input, topic):
        relevant_text = self.get_relevant_text(input, topic)
        data = self.get_relevant_pinecone_data(relevant_text)

        prompt = "Using the following source, verify that the text is up accurate."
        total_prompt = prompt + f' Source: {data}' + f' Text: {relevant_text}'
        response = self.llm.run(total_prompt)
        return response



       


        