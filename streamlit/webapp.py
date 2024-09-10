import streamlit as st
from data_processor import process_healthychildren_articles, json_loader
from crawler import scrape_conditions
from model import create_retriever, create_chain, get_npcb_response
from langchain_core.prompts import PromptTemplate
import time

condition_url = 'https://www.healthychildren.org/English/health-issues/conditions/'
base_url = 'https://www.healthychildren.org'
original_article_path = '../res/scraped_condition_articles.json'
cleaned_article_path = '../res/articles.json'


# Streamlit 앱 실행
def main():
    st.title("New Parent ChatBot")

    # Step 1: 사용자에게 데이터 업데이트 여부 묻기
    update = st.selectbox("기사 자료를 업데이트 하시겠습니까?", (" ", "예(30분 소요)", "아니오(기존 자료 사용)"))

    while update == " ":
        update = " "
    
    if update == "예":
        st.write("데이터를 수집하고 있습니다. 잠시만 기다려 주세요...")
        # 데이터 수집 및 전처리 코드 실행
        with st.spinner("데이터 수집 중..."):
            scrape_conditions(base_url, condition_url, path_to_save=original_article_path)
            process_healthychildren_articles(original_article_path, cleaned_article_path)
        st.success("데이터 수집 및 전처리가 완료되었습니다.")
    elif update == "아니오":
        st.write("기사 자료 업데이트를 건너뛰고 다음 단계로 넘어갑니다.")
    
    # Step 2: 챗봇 로딩 및 정보 제공
    st.write("이 챗봇은 healthychildren.org를 바탕으로 만들어졌으며, 의료적 책임을 지지 않습니다.")

    # 참고자료(JSON) Document list로 로드
    documents = json_loader(cleaned_article_path)

    with st.status("챗봇을 로드하고 있습니다..."):

        # 임베딩 및 검색기 생성
        retriever = create_retriever(documents)

        # 시스템 프롬프트 작성
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

        # Chain 생성
        chain = create_chain(prompt, retriever)

        # Step 3: 사용자 입력 처리 및 대화 표시
        chat_history = st.session_state.get('chat_history', [])

    st.write("질문을 입력하고 엔터를 눌러주세요.")
    user_input = st.text_input("질문을 입력하세요:")

    if user_input:
        # 챗봇 응답 생성
        response = get_npcb_response(chain, user_input)
        # 대화 내역 저장
        chat_history.append({"user": user_input, "bot": response})
        st.session_state['chat_history'] = chat_history

    # 채팅 기록 표시
    if chat_history:
        st.write("### 대화 기록")
        for i, entry in enumerate(chat_history):
            st.write(f"**사용자**: {entry['user']}")
            st.write(f"**챗봇**: {entry['bot']}")
            st.write("---")


if __name__ == "__main__":
    main()
