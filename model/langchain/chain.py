from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
    
class RAGChain:
    def __init__(self, prompt_template, model='gpt-4o'):
        # prompt_template에 {type}, {query}, {context}
        # 1. Chain Component 정의
        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_template),
            ("human", "{query}")
        ])
        llm = ChatOpenAI(model=model)
        # 2. Chain 생성
        self.chain = prompt | llm
        self.session_storage = {}   # 대화기록을 저장, 관리할 딕셔너리
    
    def get_session_history(self, session_id: str) -> InMemoryChatMessageHistory:
        if session_id not in self.session_storage:
            self.session_storage[session_id] = InMemoryChatMessageHistory()
            return self.session_storage[session_id ]
        
        # memory 객체로 불러오기
        memory = ConversationBufferMemory(
            chat_memory=self.session_storage[session_id],
            return_messages=True,
        )
        assert len(memory.memory_variables) == 1    # 메모리에 저장된 변수가 하나인지 확인
        key = memory.memory_variables[0]
        messages = memory.load_memory_variables({})[key]
        self.session_storage[session_id] = InMemoryChatMessageHistory(messages=messages)
        return self.session_storage[session_id]

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