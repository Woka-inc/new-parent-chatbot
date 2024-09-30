from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_openai import ChatOpenAI

class RetrieverWithOpenAiEmbeddings:
    def __init__(self, documents, openai_api_key):
        # 원본 문서
        self.documents = documents
        # 임베딩 모델
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large", api_key=openai_api_key)
        # 벡터스토어
        self.vectorstore = FAISS.from_documents(documents=documents, embedding=self.embeddings)
        # MutiQueryRetriever에 사용할 LLM
        llm = ChatOpenAI(temperature=0, model='gpt-4o')
        # 검색기
        self.retriever = self.vectorstore.as_retriever()
        self.multiquery_retriever = MultiQueryRetriever.from_llm(
            retriever=self.retriever,
            llm=llm
        )

        