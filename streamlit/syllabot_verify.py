import streamlit as st
import pandas as pd
import numpy as np
import os
from streamlit_chat import message
import openai

from dotenv import load_dotenv

load_dotenv()

##TODO use langchain pinecone client to implement flow here

## 
st.title('Syllabot Verification')

try:
    openai_api_key = os.getenv('OPENAI_API_KEY')
except:
    openai_api_key = None
    raise Exception('OPENAI_API_KEY not found in environment variables')

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

with st.sidebar:
    st.markdown("""
    ## About this App
    This app is a demo of using Pinecone to implement a chatbot. That processes a user's  course content and determines if it needs to be updated.
    """)

with st.form("chat_input", clear_on_submit=True):
    a, b = st.columns([4, 1])
    user_input = a.text_input(
        label="Your message:",
        placeholder="What would you like to say?",
        label_visibility="collapsed",
    )
    b.form_submit_button("Send", use_container_width=True)

for msg in st.session_state["messages"]:
    message(msg["content"], is_user=msg["role"] == "user")

    
if user_input and openai_api_key:
    openai.api_key = openai_api_key
    st.session_state.messages.append({"role": "user", "content": user_input})
    message(user_input, is_user=True)
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=st.session_state.messages)
    msg = response.choices[0].message
    st.session_state.messages.append(msg)
    message(msg.content)