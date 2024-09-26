import streamlit as st
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
import openai

from data_loader.json_loader import JsonLoader
from data_loader.datasaver import JsonSaver
from crawler.korean_hospitals import SamsungHospital, AsanMedicalCenter, SeveranceHospital
from preprocessor.structured_data import JsonToLangChainDoc
from preprocessor.embedding import RetrieverWithOpenAiEmbeddings
from model.langchain.chain import RagHistoryChain
from database.operations import save_symptom_to_db, fetch_symptom_history, add_child_to_db, fetch_all_children, delete_child, update_child

import os
import re

def update_references(bot_status, references):
    """
    참고 자료 다운로드: 삼성, 아산, 세브란스 병원의 질환 관련 컨텐츠를 Json으로 저장
    """
    print(">>> 3병원 자료 업데이트 시작함~")
    path_to_save = './res/'
    datas = []
    bot_status.update(label="정보를 업데이트 하고 있습니다.", state="running")
    
    # 데이터 크롤링 (references 리스트 순서대로)
    crawler_asan = AsanMedicalCenter()
    datas.append(crawler_asan.get_crawled_data())
    cralwer_samsung = SamsungHospital()
    datas.append(cralwer_samsung.get_crawled_data())
    cralwer_severance = SeveranceHospital()
    datas.append(cralwer_severance.get_crawled_data())

    # json으로 저장
    jsonsaver = JsonSaver()
    for i in range(len(references)):
        path = path_to_save + references[i] + '.json'
        jsonsaver.save(path, datas[i])

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

@st.dialog("수정할 아이의 정보를 입력해주세요.")
def question_update_info():
    if 'name_to_update' in st.session_state:
        st.subheader(f"{st.session_state['name_to_update']}의 정보를 수정합니다.")
        st.session_state['update_needed'] = True

    st.session_state['child_name'] = st.text_input("아이의 새로운 이름을 입력하세요.")
    st.session_state['birth_date'] = st.text_input("아이의 새로운 생년월일을 입력하세요 (예: 2020-01-01)")
    if st.button("수정"):
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

@st.dialog("등록된 아이의 정보 수정/삭제하기")
def get_childname_to(operation):
    st.write("아이의 등록정보를 수정/삭제하면,")
    st.write("저장되어있던 증상 기록 정보도 함께 수정/삭제됩니다.")
    all_children = fetch_all_children()
    names = []
    births = []
    for record in all_children:
        names.append(record[1])
        births.append(str(record[2]))
    selected = st.radio(
        label="데이터베이스에서 수정/삭제할 아이의 이름을 선택하세요.",
        options=names,
        captions=births,
        label_visibility='collapsed',
        index=None
    )
    if st.button(operation):
        st.session_state["name_to_"+operation] = selected
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

@st.dialog("Database Password")
def ask_database_pw():
    st.write(f"Database 비밀번호가 필요합니다.")
    st.write("\'확인\'버튼을 누른 후 잠시만 기다려주세요.")
    pw = st.text_input("root 비밀번호")
    if st.button("확인"):
        print(">> 사용자로부터 키 입력됨")
        st.session_state['DB_PASSWORD'] = pw
        with open("./database/config.py", "a") as config_file:
            config_file.write(f"\nDB_PASSWORD = '{pw}'")
        st.rerun()

if 'DB_PASSWORD' not in st.session_state:
    with open("./database/config.py", "r") as config_file:
        result = config_file.read()
        pw = re.search(r'DB_PASSWORD = (.+)', result)
        if pw == None:
            ask_database_pw()
        else:
            st.session_state['DB_PASSWORD'] = pw.group(1)

    # if openai.api_key:
    #     print(">> 세션에 OpenAI API에 저장되어있던 키 넣습니다요~~")
    #     st.session_state['OPENAI_API_KEY'] = openai.api_key
    # else:
    #     try:
    #         load_dotenv()
    #         OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    #         if OPENAI_API_KEY:
    #             st.session_state['OPENAI_API_KEY'] = OPENAI_API_KEY
    #             print(f">> 환경변수에서 로드해서, 세션에 저장함")
    #         else:
    #             raise ValueError(">> 환경변수에 OPENAI_API_KEY 없음. 사용자에게 요청")
    #     except ValueError as e:
    #         print(str(e))
    #         ask_api_key()

def main():
    child_name, birth_date, child_in_db = None, None, None
    references = ['asan', 'samsung', 'severance']

    print(">>> ----------- MAIN 함수 ----------- <<<")
    api_key = st.session_state['OPENAI_API_KEY']
    openai.api_key = api_key    # OpenAI API에 키 저장
    st.markdown("<h1 style='text-align: center;'>New Parent ChatBot</h1>", unsafe_allow_html=True)
    st.markdown("<h5 style='text-align: center;'>초보 부모들을 위한 의료지식 챗봇</h5>", unsafe_allow_html=True)

    # 사이드바 설정 ------------------------------------------
    st.sidebar.title("설정")

    # 참고자료 업데이트
    bot_status = st.sidebar.status(label="ChatBot Status", state="complete")
    st.sidebar.write('---')
    option = st.sidebar.selectbox('참고 자료', ('기존 자료 사용', '업데이트'))
    if option == '업데이트':
        st.cache_resource.clear()   # 캐싱된 기존 체인 삭제
        update_references(bot_status, references)
    st.sidebar.write('---')
    # 세션기록 삭제
    if st.sidebar.button("처음부터 시작하기"):
        st.session_state.clear()
        st.rerun()
    
    # 데이터 관리 섹션
    st.sidebar.subheader("데이터 관리")
    # 데이터베이스의 아이 기록 삭제
    if st.sidebar.button("아이 정보 삭제"):
        get_childname_to('delete')
    if 'name_to_delete' in st.session_state:
        name_to_del = st.session_state['name_to_delete']
        delete_child(name_to_del)
        st.session_state.pop('name_to_delete', None)
        if st.session_state['child_name'] == name_to_del:
            # 직전에 질문한 아이의 정보를 삭제한 거라면 세션 새로 시작
            st.session_state.clear()
            st.rerun()
    # 데이터베이스의 아이 정보 수정
    if st.sidebar.button("아이 정보 수정"):
        get_childname_to('update')
    if 'name_to_update' in st.session_state:
        name_to_update = st.session_state['name_to_update']
        if 'update_needed' in st.session_state:
            update_child(name_to_update, st.session_state['child_name'], st.session_state['birth_date'])
            st.session_state.pop('update_needed', None)
            st.session_state.pop('name_to_update', None)
        else:
            question_update_info()
    
    # RAG reference 자료 로드 ------------------------------------------
    resource_path = './res/'
    documents = []
    paths = [(resource_path + hospital + '.json') for hospital in references]
    
    # 다운받은 reference 자료가 없는 경우 자동 다운로드
    need_download = False
    for path in paths:
        if os.path.exists(path): continue
        else: 
            print(">>> 근거자료 파일 없음 다운로드 필요")
            need_download = True
    if need_download:
        update_references(bot_status, references)
    for path in paths:
        json_data = JsonLoader(path).load()
        documents += JsonToLangChainDoc(json_data).get_langchain_doc()

    # chain 생성 후 세션에 저장해 사용 --------------------------------------
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