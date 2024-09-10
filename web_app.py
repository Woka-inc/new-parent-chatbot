import streamlit as st
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

from data_loader.json_loader import JsonLoader
from data_loader.datasaver import JsonSaver
from crawler.healthy_children import HealthyChildrenOrg
from preprocessor.structured_data import JsonToLangChainDoc
from preprocessor.embedding import RetrieverWithOpenAiEmbeddings
from model.langchain.chain import RagHistoryChain

import os

cleaned_article_path = './res/articles.json'

def update_articles(bot_status):
    bot_status.update(label="정보를 업데이트 하고 있습니다. (최대 40분 소요)", state="running")
    crawler = HealthyChildrenOrg(cleaned_article_path)
    crawled_data = crawler.get_condition_articles_list()
    JsonSaver(cleaned_article_path, crawled_data).save()
    bot_status.update(label="정보를 업데이트 했습니다.", state="complete")

def initialize_chain(documents):
    # Embeddings
    embedding = RetrieverWithOpenAiEmbeddings(documents)
    # Vector Store
    retriever = embedding.retriever()

    prompt = PromptTemplate.from_template(
                """You are an expert in infant and toddler medical knowledge. 
                You are here to guide new parents on how to handle situations like emergencies with information from the context.
                You need to ask questions to the user if you need.
                You should answer in Korean.
                Your answer should be 1~5 sentences long unless the user ask you for longer answer.
                
                # Previous Chat History:
                {chat_history}
                
                # Question:
                {question}

                #Context: 
                {context}

                #Answer:"""
            )
    chain = RagHistoryChain(prompt, retriever, model_name='gpt-3.5-turbo')
    
    return chain

def main():
    st.markdown("<h1 style='text-align: center;'>New Parent ChatBot</h1>", unsafe_allow_html=True)
    st.markdown("<h5 style='text-align: center;'>초보 부모들을 위한 의료지식 챗봇</h5>", unsafe_allow_html=True)

    # 사이드바 설정
    st.sidebar.title("설정")

    # 사이드바: OpenAI API Key 로드
    load_dotenv()
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    if not OPENAI_API_KEY:
        api_key_input = st.sidebar.text_input("OpenAI API Key가 필요합니다.", key='api_key_input')
        OPENAI_API_KEY = api_key_input
        st.sidebar.write('---')
    # print(OPENAI_API_KEY)

    # 사이드바: 참고자료 업데이트
    bot_status = st.sidebar.status(label="ChatBot Status", state="complete")
    st.sidebar.write('---')
    option = st.sidebar.selectbox('참고 자료 선택', ('기존 자료 사용', '업데이트(40분 소요)'))
    if option == '업데이트(40분 소요)':
        update_articles(bot_status)
    st.sidebar.write('---')

    # 사이드바: 세션기록 삭제
    if st.sidebar.button("세션 기록 삭제"):
        st.session_state.clear()
        st.rerun()

    # RAG 자료 로드
    json_loader = JsonLoader(cleaned_article_path)
    json_data = json_loader.load()
    documents = JsonToLangChainDoc(json_data).get_langchain_doc()

    # chain 생성
    bot_status.update(label="loading...", state='running')
    if 'chain' not in st.session_state:
        st.session_state['chain'] = initialize_chain(documents)
    bot_status.update(label="ready", state='complete')

    # chat history 초기화
    if 'history' not in st.session_state:
        st.session_state['history'] = []
    
    if 'generated' not in st.session_state:
        st.session_state['generated'] = []
    
    if 'past' not in st.session_state:
        st.session_state['past'] = []

    # chat history와 사용자 입력을 받을 컨테이너
    response_container = st.container()
    container = st.container()

    # 사용자 입력 폼
    with container:
        user_input = st.chat_input("입력하세요..")

        if user_input:
            bot_status.update(label="loading...", state='running')
            response = st.session_state['chain'].get_response(user_input)
            st.session_state['past'].append(user_input)
            st.session_state['generated'].append(response)
            bot_status.update(label="ready", state='complete')

    # 채팅 히스토리 표시
    if st.session_state['generated']:
        with response_container:
            for i in range(len(st.session_state['generated'])):
                st.chat_message("user").write(st.session_state['past'][i])
                st.chat_message("ai").write(st.session_state['generated'][i])

if __name__ == '__main__':
    main()