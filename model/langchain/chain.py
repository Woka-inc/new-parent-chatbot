from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
    
class RAGChain:
    def __init__(self, prompt_template, model='gpt-4o'):
        # prompt_template에 {type}, {query}, {context}
        # 1. Chain Component 정의
        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_template),
            ("system", "chat_history를 참고해서 답하시오"),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{query}")
        ])
        llm = ChatOpenAI(model=model)
        # 2. Chain 생성
        self.chain = prompt | llm
        self.session_storage = {}   # 대화기록을 저장, 관리할 딕셔너리

    def get_session_history(self, session_ids: str) -> BaseChatMessageHistory:
        print(f">>> session_ids for chat history: {session_ids}")
        if session_ids not in self.session_storage:
            self.session_storage[session_ids] = ChatMessageHistory()
        return self.session_storage[session_ids]    # 해당 세션ID의 세션 기록(ChatMessageHistory객체) 반환

    def get_response(self, query, query_type, context, session_ids):
        with_msg_history = RunnableWithMessageHistory(
            self.chain,  # 실행할 runnable 객체
            self.get_session_history,
            input_messages_key="query",  # 최신 입력 메세지로 처리되는 키
            history_messages_key="chat_history" # 이전 메세지를 추가할 키
        )
        response = with_msg_history.invoke(
            {
            'type': query_type,
            'query': query,
            'context': context
            },
            config={"configurable": {"session_id": session_ids}}
        )
        return response.content