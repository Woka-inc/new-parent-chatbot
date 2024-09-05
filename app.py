from data_processor import process_healthychildren_articles, json_loader
from crawler import scrape_conditions
from model import create_retriever, create_chain, get_npcb_response

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate


condition_url = 'https://www.healthychildren.org/English/health-issues/conditions/'
base_url = 'https://www.healthychildren.org'
original_article_path = './res/scraped_condition_articles.json'
cleaned_article_path = './res/articles.json'

if __name__ == "__main__":
    # 데이터 크롤링 여부 확인
    do_crawl = input("기사자료를 새로 크롤링 하시겠습니까? y/n: ")
    print("New Parent ChatBot을 로딩 중입니다.")
    if do_crawl == 'y':
        # 데이터 수집, 전처리
        scrape_conditions(base_url, condition_url, path_to_save=original_article_path)
        process_healthychildren_articles(original_article_path, cleaned_article_path)
    
    # 참고자료(JSON) Document list로 로드
    documents = json_loader(cleaned_article_path)

    # 임베딩, 검색기 생성
    retriever = create_retriever(documents)

    # system 프롬프트 작성
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

    # chain 생성
    chain = create_chain(prompt, retriever)

    # 사용자 입력 처리 루프
    for user_input in iter(lambda: input("질문을 입력하세요 ('exit'를 입력하면 종료됩니다): "), "exit"):
        response = get_npcb_response(chain, user_input)
        print(">> ChatBot: ", response)

    print("New Parent ChatBot을 종료합니다.")
