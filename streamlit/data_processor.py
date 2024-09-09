import json
from bs4 import BeautifulSoup
from langchain.docstore.document import Document

# HTML 태그를 제거하고 순수 텍스트만 남기기 위한 함수
def clean_html(html_content):
    soup = BeautifulSoup(html_content, 'lxml')
    return soup.get_text(separator='\n').strip()

def replace_threelines(text):
    return text.replace('\n\n\n', '\t ').strip()

# 텍스트에서 \r과 \n을 제거하는 함수
def remove_newlines(text):
    return text.replace('\r', '').replace('\n', ' ').strip()

# JSON파일을 읽고 처리하는 함수
def process_healthychildren_articles(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    cleaned_data = []

    # 각 condition과 기사를 순회하며 HTML 정제
    for condition, articles in data.items():
        for title, content in articles.items():
            cleaned_article = {}
            cleaned_content = clean_html(content)
            no_threelines_content = replace_threelines(cleaned_content)
            no_newlines_content = remove_newlines(no_threelines_content)
            cleaned_article['content'] = no_newlines_content
            cleaned_article['metadata']={}
            cleaned_article['metadata']['title']=title
            cleaned_article['metadata']['condition']=condition
            
            cleaned_data.append(cleaned_article)
        
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=4)


def json_loader(path):
    # JSON 파일 로드
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # JSON 데이터에서 문서 추출
    documents = [
        Document(page_content=doc['content'], metadata=doc['metadata'])
        for doc in data
    ]

    return documents