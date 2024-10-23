from langchain.docstore.document import Document

def json_to_langchain_doclist(datas_in_json):
    documents = [
        Document(page_content=doc['content'], metadata=doc['metadata'])
        for doc in datas_in_json
    ]
    return documents