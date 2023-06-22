import pinecone
import openai
import os

import langchain
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQAWithSourcesChain

from langchain.vectorstores import Pinecone

openai_api_key = os.getenv('OPENAI_API_KEY')
pinecone_api_key = os.getenv('PINECONE_API_KEY')

class LangChainPineconeClient:
    def __init__(self, pinecone_key = pinecone_api_key, openai_key = openai_api_key):
        ## Initialize with Pinecone API key and OpenAI API key
        pinecone.init(api_key=pinecone_key, environment='us-west4-gcp-free')
        openai.api_key = openai_key


    def view_indexes(self):
        ## View all indexes
        return pinecone.list_indexes()
    
    def get_relevant_text(input, topic = "LangChain"):
        ## Get relevant text from input_text
        prompt = f'Extract text relevant to {topic} from the following document'
        response = openai.Answer.create(
            search_model="ada",
            model="curie",
            question=prompt+input,
            examples_context=input,
            max_rerank=10,
            max_tokens=100,
        )
        return response
    
    def get_relevant_pinecone_data(self, input):

        