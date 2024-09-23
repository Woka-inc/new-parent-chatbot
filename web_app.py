import streamlit as st
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
import openai

from data_loader.json_loader import JsonLoader
from data_loader.datasaver import JsonSaver
from crawler.healthy_children import HealthyChildrenOrg
from preprocessor.structured_data import JsonToLangChainDoc
from preprocessor.embedding import RetrieverWithOpenAiEmbeddings
from model.langchain.chain import RagHistoryChain
from database.operations import save_symptom_to_db, fetch_symptom_history, add_child_to_db, fetch_all_children

import os

cleaned_article_path = './res/articles.json'

def update_articles(bot_status):
    bot_status.update(label="정보를 업데이트 하고 있습니다. (최대 40분 소요)", state="running")
    crawler = HealthyChildrenOrg(cleaned_article_path)
    crawled_data = crawler.get_condition_articles_list()
    JsonSaver(cleaned_article_path, crawled_data).save()
    bot_status.update(label="정보를 업데이트 했습니다.", state="complete")

@st.cache_resource
def initialize_chain(_documents, openai_api_key):
    # Embeddings
    embedding = RetrieverWithOpenAiEmbeddings(_documents, openai_api_key=openai_api_key)
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
    chain = RagHistoryChain(prompt, retriever, openai_api_key=openai_api_key, model_name='gpt-3.5-turbo')
    
    return chain

def get_child_info(name):
    all_children = fetch_all_children()
    if all_children:
        for record in all_children:
            if record[1] == name: # record[1]이 아이의 이름에 해당
                return record
    return None

def create_query_with_symptoms(birth, symptom, description, history):
    # 챗에서 사용자의 말풍선으로 표시될 사용자의 증상 입력 내용
    symptom_input = f"""
    - 아이의 생년월일: {birth}
    - 증상: {symptom}
    - 증상에 대한 설명: {description}
    """

    # 실제 모델에게 전달될, 과거 증상 내역을 포함한 사용자의 증상 입력 내용
    query = f"""
    I observe the symptom below from my child.
    - birth of this child: {birth}
    - observed symptoms: {symptom}
    - descriptions on observed symptoms: {description}

    Here is the past symptoms that I recorded before.
    - recorded past symptoms of this child: {history}

    Please tell me what I can do immediately.
    Visiting a hospital is not an option right now.
    If you made judgement based on the recorded past symptoms, tell me that you did so.
    """
    return symptom_input, query

def generate_chat(bot_status, query, child_name, query_to_show=None):
    if not query_to_show:
        # 증상입력이 아닌 chat_input을 통한 사용자 입력의 경우 입력 내용을 그대로 표시
        query_to_show = query
    bot_status.update(label='loading...', state='running')
    response = st.session_state['chain'].get_response(query, session_id=child_name)
    # 사용자 입력과 응답 내용을 세션기록에 추가
    st.session_state['past'].append(query_to_show)
    st.session_state['generated'].append(response)
    bot_status.update(label='ready', state='complete')

@st.dialog("증상 입력하기")
def submit_symptoms(child_name, birth_date, history, bot_status):
    symptom = st.text_input("아이의 증상을 입력하세요.")
    description = st.text_area("증상을 설명해주세요.")

    if st.button("증상 저장 후 챗봇에게 물어보기"):
        save_symptom_to_db(child_name, symptom, description)
        symptom_input, query = create_query_with_symptoms(birth_date,
                                                        symptom,
                                                        description,
                                                        history)
        generate_chat(bot_status,
                        query,
                        child_name,
                        query_to_show=symptom_input)
        st.session_state['submitted_symptom'] = True
        st.rerun()

@st.dialog("아이의 정보를 입력해주세요.")
def question_child_info():
    st.markdown("<span style='font-weight:bold;'>아이의 이름을 입력하세요.</span>", unsafe_allow_html=True)
    child_name = st.text_input("동명이인 등록 불가")
    if child_name:
        child_in_db = get_child_info(child_name)
        st.session_state['child_name'] = child_name
        print(f"세션에 저장됨: {st.session_state['child_name']}")

        if child_in_db:
            birth_date = child_in_db[2]
            st.write("생년월일: ", birth_date)
            st.session_state['birth_date'] = birth_date
            if st.button("확인"):
                    st.rerun()
            
        else:
            birth_date = st.text_input("생년월일 (예: 2020-01-01)")
            st.session_state['birth_date'] = birth_date
            if birth_date:
                add_child_to_db(child_name, birth_date)
                st.write("아이를 데이터베이스에 등록했습니다.")
        
                if st.button("확인"):
                    st.rerun()

@st.dialog("OpenAI API Key")
def ask_api_key():
    st.write(f"OpenAI API Key가 필요합니다.")
    st.write("\'확인\'버튼을 누른 후 잠시만 기다려주세요.")
    key = st.text_input("sk-...")
    if st.button("확인"):
        print(">> 사용자로부터 키 입력됨")
        st.session_state['OPENAI_API_KEY'] = key
        st.rerun()

if 'OPENAI_API_KEY' not in st.session_state:
    if openai.api_key:
        print(">> 세션에 OpenAI API에 저장되어있던 키 넣습니다요~~")
        st.session_state['OPENAI_API_KEY'] = openai.api_key
    else:
        try:
            load_dotenv()
            OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
            if OPENAI_API_KEY:
                st.session_state['OPENAI_API_KEY'] = OPENAI_API_KEY
                print(f">> 환경변수에서 로드해서, 세션에 저장함")
            else:
                raise ValueError(">> 환경변수에 OPENAI_API_KEY 없음. 사용자에게 요청")
        except ValueError as e:
            print(str(e))
            ask_api_key()

def main():
    child_name, birth_date, child_in_db = None, None, None

    print(">>> ----------- MAIN 함수 ----------- <<<")
    api_key = st.session_state['OPENAI_API_KEY']
    openai.api_key = api_key    # OpenAI API에 키 저장
    st.markdown("<h1 style='text-align: center;'>New Parent ChatBot</h1>", unsafe_allow_html=True)
    st.markdown("<h5 style='text-align: center;'>초보 부모들을 위한 의료지식 챗봇</h5>", unsafe_allow_html=True)

    # 사이드바 설정
    st.sidebar.title("설정")

    # 사이드바: 참고자료 업데이트
    bot_status = st.sidebar.status(label="ChatBot Status", state="complete")
    st.sidebar.write('---')
    option = st.sidebar.selectbox('참고 자료 선택', ('기존 자료 사용', '업데이트(40분 소요)'))
    if option == '업데이트(40분 소요)':
        st.cache_resource.clear()   # 캐싱된 기존 체인 삭제
        update_articles(bot_status)
    st.sidebar.write('---')
    # 사이드바: 세션기록 삭제
    if st.sidebar.button("처음부터 시작하기"):
        st.session_state.clear()
        st.rerun()

    # RAG 자료 로드
    json_loader = JsonLoader(cleaned_article_path)
    json_data = json_loader.load()
    documents = JsonToLangChainDoc(json_data).get_langchain_doc()

    # chain 생성 후 세션에 저장해 사용
    bot_status.update(label="loading...", state='running')
    if 'chain' not in st.session_state:
        st.session_state['chain'] = initialize_chain(documents, api_key)
    bot_status.update(label="ready", state='complete')

    # 사용자 질문 세션상태 초기화
    if 'past' not in st.session_state:
        st.session_state['past'] = []

    # 질문에 대한 응답 세션상태 초기화
    if 'generated' not in st.session_state:
        st.session_state['generated'] = []
    
    # 증상 입력 여부 초기화
    if 'submitted_symptom' not in st.session_state:
        st.session_state['submitted_symptom'] = False

    # 아이 이름과 생년월일 입력받기 혹은 로드
    if 'child_name' not in st.session_state:
        question_child_info()
    else:
        child_name = st.session_state['child_name']
        birth_date = st.session_state['birth_date']
        child_in_db = get_child_info(child_name)
        print(f">> 세션 아이 정보: {child_name, birth_date}")

    # 아이 정보 영역
    child_info_row = st.columns(2)
    chat_container = st.container(border=True)
    response_container = st.container()
    chat_input_container = st.container(border=True)

    with child_info_row[0].container(border=True):
            st.markdown(f"이름: <b>{child_name}</b>", unsafe_allow_html=True)
            st.markdown(f"생년월일: <b>{birth_date}</b>", unsafe_allow_html=True)

    with child_info_row[1].container(border=True):
        st.markdown("<span style='font-weight:bold;'>히스토리</span>", unsafe_allow_html=True)
        if child_in_db :
            his_her_history = fetch_symptom_history(child_in_db[1])
            for record in his_her_history:
                recorded_at = record[4]
                recorded_symptom = record[2]
                st.write(f"[ {recorded_at} ] {recorded_symptom}")

    if st.button("증상 입력하기"):
        submit_symptoms(child_name, birth_date, his_her_history, bot_status)

    # 증상이 입력된 후에 chat_input 띄우기
    with chat_input_container:
        if st.session_state['submitted_symptom']:
            user_input = st.chat_input("궁금한 점을 입력하세요.")
            if user_input:
                generate_chat(bot_status, user_input, child_name)

    # 채팅 히스토리 표시
    with chat_container:
        if st.session_state['generated']:
            with response_container:
                for i in range(len(st.session_state['generated'])):
                    st.chat_message("user").write(st.session_state['past'][i])
                    st.chat_message("ai").write(st.session_state['generated'][i])

if __name__ == '__main__':
    if 'OPENAI_API_KEY' in st.session_state:
        main()