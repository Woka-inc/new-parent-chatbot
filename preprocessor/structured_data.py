from langchain.docstore.document import Document

class JsonToLangChainDoc:
    def __init__(self, data):
        # 원본 Json인 data는 'content'와 'metadata'라는 키로 구성된 딕셔너리
        # https://api.python.langchain.com/en/latest/documents/langchain_core.documents.base.Document.html
        self.data = data
    
    def get_langchain_doc(self):
        documents = [
            Document(page_content=doc['content'], metadata=doc['metadata'])
            for doc in self.data
        ]
        return documents