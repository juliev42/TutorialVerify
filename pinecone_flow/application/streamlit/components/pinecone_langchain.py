import pinecone
import openai
import os

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

openai_api_key = os.getenv('OPENAI_API_KEY')
pinecone_api_key = os.getenv('PINECONE_API_KEY')
pinecone_index_name = os.getenv('PINECONE_INDEX_NAME')
pinecone_environment = os.getenv('PINECONE_ENV')

class LangChainPineconeClient:
    def __init__(self, pinecone_key = pinecone_api_key, openai_key = openai_api_key, index_name=pinecone_index_name):
        ## Initialize with Pinecone API key and OpenAI API key, plus relevant index name
        pinecone.init(api_key=pinecone_key, environment=pinecone_environment)
        openai.api_key = openai_key

        index = pinecone.Index(index_name)
        self.index = index
        text_field = "text" #name of metadata field that contains text

        embed = OpenAIEmbeddings(
            model='text-embedding-ada-002',
            openai_api_key=openai_api_key
        )
        self.embed = embed


        self.vectorstore = Pinecone(
            index, embed.embed_query, text_field
        )

        self.llm = ChatOpenAI(
            openai_api_key=openai_api_key,
            model_name='gpt-3.5-turbo',
            temperature=0.0)
        


        self.messages = [SystemMessage(content="You are a helpful assistant.")]


    def view_indexes(self):
        ## View all indexes
        return pinecone.list_indexes()
    
    def get_relevant_text(self, input, topic = "LangChain or prompting LLMs with chains of text"):
        ## Get relevant text from input_text
        prompt = f'Extract text relevant to {topic} from the following document ' + input
        first_message = HumanMessage(content=prompt)
        self.messages.append(first_message)
        response = self.llm(self.messages)
        self.messages.append(response)
        return response
    
    def get_relevant_pinecone_data(self, input):
        ## TODO rewrite this + init to use pinecone query instead of langchain package
        qa_response = self.qa.run(input)
        return qa_response
    
    def ask_with_context(self, input, topic):
        relevant_text = self.get_relevant_text(input, topic)
        data = self.get_relevant_pinecone_data(relevant_text)

        prompt = "Using the following source, verify that the text is up accurate."
        total_prompt = prompt + f' Source: {data}' + f' Text: {relevant_text}'
        context_ask = HumanMessage(content=total_prompt)
        self.messages.append(context_ask)
        response = self.llm(total_prompt)
        self.messages.append(response)
        return response
    
    def create_syllabus_content(self, input, topic):
        pass

    def check_syllabus(self, syllabus):
        pass




       


        