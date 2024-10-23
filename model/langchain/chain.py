from operator import itemgetter
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

class RagHistoryChain:
    def __init__(self, prompt, retriever, openai_api_key, model_name="gpt-4o"):
        llm = ChatOpenAI(model_name=model_name, api_key=openai_api_key)
        self.chain = (
            {
            "context": itemgetter("question") | retriever,
            "question": itemgetter("question"),
            "chat_history": itemgetter("chat_history")
            }
            | prompt
            | llm
            | StrOutputParser()
        )
        self.session_storage = {}
    
    def get_session_history(self,session_id=1):
        print(f"[대화 세션ID]: {session_id}")
        if session_id not in self.session_storage:  # 세션 ID가 session_storage에 없는 경우
            # 새로운 ChatMessageHistory 객체를 생성하여 session_storage에 저장
            self.session_storage[session_id] = ChatMessageHistory()
        return self.session_storage[session_id]  # 해당 세션 ID에 대한 세션 기록 반환
    
    def get_response(self, question, ragged_docs, session_id=1):
        # 대화를 기록하는 RAG체인 생성
        rag_with_history = RunnableWithMessageHistory(
            self.chain,
            self.get_session_history, # 세션 기록 가져오는 메서드
            input_messages_key="question", # 사용자의 질문을 담아 템플릿 변수로 들어갈 key
            history_messages_key="chat_history" # 기록 메세지의 key
        )
        response = rag_with_history.invoke(
            # 질문 입력
            {"question": question},
            # 세션 ID 기준으로 대화 기록
            config={"configurable": {"session_id": session_id}}
        )
        return response
    
class RAGChain:
    def __init__(self, prompt_template, model='gpt-4o'):
        # 1. Chain Component 정의
        prompt = ChatPromptTemplate.from_template(prompt_template)
        llm = ChatOpenAI(model=model)
        # 2. Chain 생성
        self.chain = prompt | llm

    def get_response(self, query, query_type, context):
        response = self.chain.invoke({
            'type': query_type,
            'query': query,
            'context': context
        })
        return response.content