import time

import requests
from tqdm import tqdm
from bs4 import BeautifulSoup

class HealthyChildrenOrg:
    def __init__(self, path_to_save):
        self.base_url = 'https://www.healthychildren.org'
        self.path_to_save = path_to_save
    
    def get_condition_articles_list(self):
        condition_url = 'https://www.healthychildren.org/English/health-issues/conditions/'
        result = {}

        # conditions 페이지에서 모든 condition들의 링크 찾기
        response = requests.get(condition_url)
        soup = BeautifulSoup(response.content, 'lxml')

        # 1. condition 항목(z1_QuickLaunchMenu_5를 태그명으로 갖는 모든 a태그) 찾기
        condition_links = soup.select('a.ms-navitem')

        if not condition_links:
            print("no condition links found")

        # 테스트용 코드(시간단축 목적)
        condition_links = condition_links[:1]

        # 2. 각 condition 페이지에서 기사들 링크 추출
        for condition_link in tqdm(condition_links):
            condition_name = condition_link.get_text(strip=True)
            condition_url = self.base_url + condition_link['href']
            print(f">> visited {condition_name}")

            # condition별 기사들을 저장할 딕셔너리
            condition_articles = {}

            # condition 페이지로 이동
            response = requests.get(condition_url)
            condition_soup = BeautifulSoup(response.content, 'lxml')

            # 모든 article items 찾기 in li.article-rollup-item
            article_items = condition_soup.select('li.article-rollup-item')

            # 3. 각 article 페이지에서 제목과 본문 추출
            for article_item in tqdm(article_items):
                article_title_tag = article_item.select_one('span.article-title')
                article_link_tag = article_item.select_one('a')

                if article_title_tag and article_link_tag:
                    # article_title = article_title_tag.get_text(strip=True)
                    article_url = article_link_tag['href']
                    # print(f"    >> got an article:{article_title}")

                    article_response = requests.get(article_url)
                    article_soup = BeautifulSoup(article_response.content, 'lxml')

                    # 기사 제목과 본문 추출
                    article_page_title = article_soup.select_one('h1.page-title').get_text(strip=True)
                    article_content_pieces = article_soup.select('div.ms-rtestate-field')

                    for piece in article_content_pieces:
                        if piece.find():
                            article_content = piece
                            break

                    if article_content:
                        article_html = str(article_content)
                        condition_articles[article_page_title] = article_html
                    
                    time.sleep(0.5) # 요청 간에 약간의 대기 시간을 둬서 서버에 부담을 주지 않도록 함
                
                # 모든 기사를 추출했으면 결과에 추가
                if condition_articles:
                    result[condition_name] = condition_articles
                
                time.sleep(0.5) # 컨디션 간 약간의 대기 시간
        
        # HTML과 공백을 삭제하는 전처리
        cleaned_data = []
        for condition, articles in result.items():
            for title, content in articles.items():
                cleaned_article = {}
                dirty_article_soup = BeautifulSoup(content, 'lxml')
                cleaned_content = dirty_article_soup.get_text(separator='\n').strip()
                no_threelines_content = cleaned_content.replace('\n\n\n', '\t ').strip()
                no_newlines_content = no_threelines_content.replace('\r', '').replace('\n', ' ').strip()
                cleaned_article['content'] = no_newlines_content
                cleaned_article['metadata'] = {}
                cleaned_article['metadata']['title'] = title
                cleaned_article['metadata']['condition'] = condition

                cleaned_data.append(cleaned_article)
        
        return cleaned_data