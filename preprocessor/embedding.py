from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

class RetrieverWithOpenAiEmbeddings:
    def __init__(self, documents):
        # 원본 문서
        self.documents = documents
        # 임베딩 모델
        self.embeddings = OpenAIEmbeddings()
        # 벡터스토어
        self.vectorstore = FAISS.from_documents(documents=documents, embedding=self.embeddings)
        # 검색기
        self.retriever = self.vectorstore.as_retriever