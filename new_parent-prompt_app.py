from data_loader.json_loader import JsonLoader
from data_loader.datasaver import JsonSaver
from crawler.healthy_children import HealthyChildrenOrg
from preprocessor.structured_data import JsonToLangChainDoc
from preprocessor.embedding import RetrieverWithOpenAiEmbeddings
from model.langchain.chain import RagHistoryChain

from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
import os

cleaned_article_path = './res/articles.json'

if __name__ == "__main__":

    # OpenAI API KEY 로드
    load_dotenv()
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    if not OPENAI_API_KEY:
        OPENAI_API_KEY = input("OpenAI API Key를 입력하세요: ")

    # 데이터 크롤링 여부 확인
    do_crawl = input("자료를 업데이트 하시겠습니까? y/n: ")

    if do_crawl == 'y':
        print("참고자료를 업데이트 중입니다.")
        # 데이터 수집, 저장
        healthychildren = HealthyChildrenOrg(cleaned_article_path)
        crawled_data = healthychildren.get_condition_articles_list()
        JsonSaver(cleaned_article_path, crawled_data).save()
    
    # JSON 데이터를 로드하고 LangChain Document 객체로 가져오기
    json_loader = JsonLoader(cleaned_article_path)
    json_data = json_loader.load()
    documents = JsonToLangChainDoc(json_data).get_langchain_doc()

    # print(documents[0])

    # 임베딩 후 검색기 생성
    embedding = RetrieverWithOpenAiEmbeddings(documents)
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

    # 체인 생성
    chain = RagHistoryChain(prompt, retriever)

    # 사용자 입력 처리 루프
    for user_input in iter(lambda: input("질문을 입력하세요 ('exit'를 입력하면 종료됩니다): "), "exit"):
        response = chain.get_response(user_input)
        print(">> ChatBot: ", response, "\n\n")
    
    print("New Parent ChatBot을 종료합니다.")