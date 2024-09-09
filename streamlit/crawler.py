import json
import time

import requests
from tqdm import tqdm
from bs4 import BeautifulSoup

def scrape_conditions(base_url, condition_url, path_to_save):
    start_time = time.time()
    result = {}

    # conditions 페이지에서 모든 condition들의 링크 찾기
    response = requests.get(condition_url)
    soup = BeautifulSoup(response.content, 'lxml')

    # 1. condition 항목(z1_QuickLaunchMenu_5를 태그명으로 갖는 모든 a태그) 찾기
    condition_links = soup.select('a.ms-navitem')

    if not condition_links:
        print("no condition links found")

    # 2. 각 condition 페이지에서 기사들 링크 추출
    for condition_link in tqdm(condition_links):
        condition_name = condition_link.get_text(strip=True)
        condition_url = base_url + condition_link['href']
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
            
            time.sleep(0.5) # 컨디션 간에 약간의 대기 시간
    
    with open(path_to_save, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    
    end_time = time.time()
    print(f">>> Duration: {end_time - start_time}sec")


