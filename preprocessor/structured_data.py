from langchain.docstore.document import Document

class JsonToLangChainDoc:
    def __init__(self, data):
        self.data = data
    
    def get_langchain_doc(self):
        documents = [
            Document(page_content=doc['content'], metadata=doc['metadata'])
            for doc in self.data
        ]
        return documents