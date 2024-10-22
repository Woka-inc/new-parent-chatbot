from langchain_community.retrievers import BM25Retriever
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.retrievers import EnsembleRetriever

class FAISSBM25Retriever:
    def __init__(self, docs_list, openai_api_key, top_k=1):
        # BM25 검색기 설정
        bm25_retriever = BM25Retriever.from_documents(docs_list)
        bm25_retriever.k = top_k

        # FAISS 검색기 설정
        embedding = OpenAIEmbeddings(model="text-embedding-3-large", api_key=openai_api_key)
        faiss_vectorstore = FAISS.from_documents(
            documents=docs_list,
            embedding=embedding
        )
        faiss_retriever = faiss_vectorstore.as_retriever(search_kwargs={"k":top_k})

        # Ensemble 검색기 생성
        self.retriever = EnsembleRetriever(
        retrievers=[faiss_retriever, bm25_retriever], # 순차적으로 전달
        weights=[0.5, 0.5]
        )
    
    def search_docs(self, query):
        retrieved_docs = self.retriever.invoke(query)
        return retrieved_docs
    
