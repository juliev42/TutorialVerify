import pinecone
import openai
import os
import sys

import langchain
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.embeddings.openai import OpenAIEmbeddings

from langchain.schema import (
    SystemMessage,
    HumanMessage,
    AIMessage
)
from langchain.vectorstores import Pinecone
import scrapeandindex.sparsevectors as sv
import scrapeandindex.query as query_sql

import psycopg2

currentdir = os.getcwd()
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)


OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PINECONE_API_KEY= os.getenv('PINECONE_API_KEY')
PINECONE_INDEX_NAME = os.getenv('PINECONE_INDEX_NAME')
PINECONE_ENV = os.getenv('PINECONE_ENV')
DATABASE_URL = os.getenv('DATABASE_URL')

class LangChainPineconeClient:
    def __init__(self, pinecone_key = PINECONE_API_KEY, openai_key = OPENAI_API_KEY, index_name=PINECONE_INDEX_NAME, pinecone_env=PINECONE_ENV, database_url=DATABASE_URL):
        """"
        Initialize LangChainPineconeClient with Pinecone API key and OpenAI API key, plus relevant index name
        Args:
            pinecone_key (str): Pinecone API key
            openai_key (str): OpenAI API key
            index_name (str): name of Pinecone index to use
            pinecone_env (str): Pinecone environment to use
            database_url (str): URL of SQL database to use
        """
        ## Initialize with Pinecone API key and OpenAI API key, plus relevant index name
        pinecone.init(api_key=pinecone_key, environment=pinecone_env)

        index = pinecone.Index(index_name)
        self.index = index

        embed = OpenAIEmbeddings(
            model='text-embedding-ada-002',
            openai_api_key=openai_key
        )
        self.embed = embed


        self.llm = ChatOpenAI(
            openai_api_key=openai_key,
            model_name='gpt-3.5-turbo',
            temperature=0.0)
        
        ## Initialize messages for chat 
        self.messages = [SystemMessage(content="You are a helpful assistant.")]

        ## Initialize connection to SQL database
        conn = psycopg2.connect(database_url)
        self.cur = conn.cursor()

        
    def view_indexes(self):
        ## View all indexes
        pinecone.list_indexes()
    
    def get_relevant_text(self, input, topic = "LangChain or prompting LLMs with chains of text"):
        """"
        Initialize LangChainPineconeClient with Pinecone API key and OpenAI API key, plus relevant index name
        Args:
            input (str): input text from user (could be scraped from url)
            topic (str): topic of text to be extracted
        """
        prompt = f'Extract text relevant to {topic} from the following document ' + input
        first_message = HumanMessage(content=prompt)
        self.messages.append(first_message)
        response = self.llm(self.messages)
        self.messages.append(response)
        return response.content
    
    def get_relevant_pinecone_data(self, input):
        """
        Get relevant data from Pinecone index
        Args:
            input (str): extracted text from input or another input 
        Return: 
            (str): relevant text from Pinecone index with source URL
        """
        ##TODO change to return multiple sources to check against rather than just one
        embedded_query = self.embed.embed_query(input)
        query_results = self.index.query(namespace='langchaindocs', top_k=1, \
                                         vector=embedded_query, 
                                         sparse_vector = sv.get_sparse_vector(input))
        match_id = query_results['matches'][0]['id']
        data = query_sql.get_heading_by_rowid(match_id, self.cur)
        result_text = data[5]
        try: #try to get source URL if it exists
            url = query_sql.get_url_by_headingid(data[0], self.cur)
            result_text = result_text + f' Source: {url}'
        except:
            pass
        return result_text


    
    def ask_with_context(self, input, topic = "LangChain or prompting LLMs with chains of text"):
        """
            Calls get_relevant_text and get_relevant_pinecone_data to do the total text flow. 
            This is the only function that needs to be called by the frontend
            Args:
                input (str): extracted text from input or another input 
                topic (str): description of topic of text to be extracted
            Return: 
                (str): relevant text from Pinecone index with source URL
        """
        ##TODO add a function call before this to break things down into subtopics first
        relevant_text = self.get_relevant_text(input, topic)
        data = self.get_relevant_pinecone_data(relevant_text)

        prompt = "Using the following source, verify that the text is up to date and accurate."
        total_prompt = prompt + f' Source: {data}' + f' Text: {relevant_text}'
        context_ask = HumanMessage(content=total_prompt)
        self.messages.append(context_ask)
        response = self.llm(self.messages)
        self.messages.append(response)
        overall_response = response.content + f' Source: {data}'
        return overall_response


    def check_syllabus(self, syllabus):
        pass




       


        