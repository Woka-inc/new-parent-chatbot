from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from operator import itemgetter
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# 세션 기록을 저장할 딕셔너리
session_storage = {}

# 벡터화 및 검색 시스템 구축
def create_retriever(documents):
    # 임베딩 모델 로드
    embeddings = OpenAIEmbeddings()

    # 모든 문서를 임베딩
    vectorstore = FAISS.from_documents(documents=documents, embedding=embeddings)

    # 검색기 생성
    retriever = vectorstore.as_retriever()

    return retriever

# LLM, Chain with RAG, memory 생성
def create_chain(prompt, retriever, model_name="gpt-4o"):
    # LLM 생성
    llm = ChatOpenAI(model_name=model_name, temperature=0)

    # 체인 생성
    chain = (
        {
            "context": itemgetter("question") | retriever,
            "question": itemgetter("question"),
            "chat_history": itemgetter("chat_history")
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return chain

# 세션 ID를 기반으로 세션 기록을 가져오는 함수
def get_session_history(session_ids):
    print(f"[대화 세션ID]: {session_ids}")
    if session_ids not in session_storage:  # 세션 ID가 session_storage에 없는 경우
        # 새로운 ChatMessageHistory 객체를 생성하여 session_storage에 저장
        session_storage[session_ids] = ChatMessageHistory()
    return session_storage[session_ids]  # 해당 세션 ID에 대한 세션 기록 반환

# 함수화
def get_npcb_response(chain, question, session_id=1):
    # 대화를 기록하는 RAG 체인 생성
    rag_with_history = RunnableWithMessageHistory(
        chain,
        get_session_history,  # 세션 기록을 가져오는 함수
        input_messages_key="question",  # 사용자의 질문이 템플릿 변수에 들어갈 key
        history_messages_key="chat_history",  # 기록 메시지의 키
    )

    response = rag_with_history.invoke(
        # 질문 입력
        {"question": question},
        # 세션 ID 기준으로 대화 기록
        config={"configurable": {"session_id": session_id}},
        )   
    
    return response