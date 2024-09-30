import time
import re

from .base_crawler import BaseCrawler

from tqdm import tqdm
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By

class AsanMedicalCenter(BaseCrawler):
    def __init__(self):
        self.root_url = 'https://health.severance.healthcare/health/encyclopedia/disease/body_board.do'
        self.base_url = 'https://child.amc.seoul.kr/asan/depts/child/K/bbs.do?pageIndex=1&menuId=4342&contentId=259962'
    
    def get_crawled_data(self):
        # 브라우저를 띄우지 않는 옵션
        options = webdriver.ChromeOptions()
        options.add_argument("headless")
        driver = webdriver.Chrome(options=options)

        disease_urls = []
        data = []

        # 총 질환정보 링크의 개수 가져오기
        driver.get(self.base_url)
        driver.implicitly_wait(2)
        n_url = int(driver.find_element(By.CSS_SELECTOR, 'p.searchResult > span').text[:-1])
        
        # 링크 개수를 채울 때까지 다음 페이지로 넘어가며 링크 모으기
        while(len(disease_urls) < n_url):
            atags_in_page = driver.find_elements(By.CSS_SELECTOR, 'td.title > a')
            for atag in atags_in_page:
                disease_urls.append(atag.get_attribute('href'))
            
            page_atags = driver.find_elements(By.CSS_SELECTOR, 'span.numPagingSec > a')
            if (len(disease_urls) < n_url):
                for i in range(len(page_atags)):
                    if i == len(page_atags) - 1:
                        next_btn = driver.find_element(By.CSS_SELECTOR, 'a.nextPageBtn')
                    elif page_atags[i].get_attribute('class') == "nowPage":
                        next_btn = page_atags[i + 1]
                        break
                next_btn.click()
                time.sleep(1)
            
        # 각 페이지에서 정보 뽑아내기
        for url in tqdm(disease_urls):
            driver.get(url)
            driver.implicitly_wait(3)

            page_title_raw = driver.find_element(By.ID, 'viewTitle').text
            disease_name = re.search(r'\] (.+)', page_title_raw).group(1)
            disease_detail = driver.find_element(By.CSS_SELECTOR, 'td.viewContent > div.cont').text
            disease_content = disease_name + "\n\n" + disease_detail
            metadata = {'name': disease_name,
                        'source': url}
            disease = {'content': disease_content, 'metadata': metadata}
            data.append(disease)

        driver.quit()
        return data
    
class SamsungHospital(BaseCrawler):
    def __init__(self):
        self.root_url = 'http://www.samsunghospital.com/'
        self.base_url = 'http://www.samsunghospital.com/home/healthInfo/content/contentList.do?CONT_CLS_CD=001020001008'
    
    def get_crawled_data(self):
        # 브라우저를 띄우지 않는 옵션
        options = webdriver.ChromeOptions()
        options.add_argument("headless")
        driver = webdriver.Chrome(options=options)
        
        disease_urls = []

        # 목록 페이지에서 각 질병의 상세페이지 url 가져오기
        response = requests.get(self.base_url)
        soup = BeautifulSoup(response.content, 'lxml')
        disease_cards = soup.select('section.card-item-inner > a')
        for card in disease_cards:
            disease_urls.append(self.root_url + card['href'])
        # print(disease_urls[0])

        # 각 질병 페이지(동적)에서 selenium으로 크롤링하기
        data = []
        
        for url in tqdm(disease_urls):
            driver.get(url)
            driver.implicitly_wait(3)

            disease_name = driver.find_elements(By.CSS_SELECTOR, 'section.post-detail-body > strong')[0].text
            disease_detail = driver.find_elements(By.CSS_SELECTOR, 'div.cms_diseaseDetail')[0].text
            disease_content = disease_name + "\n\n" + disease_detail
            metadata = {'name': disease_name[6:],
                        'source': url}
            disease = {'content': disease_content, 'metadata': metadata}
            data.append(disease)
        
        driver.quit()
        return data
    
class SeveranceHospital(BaseCrawler):
    def __init__(self):
        self.root_url = 'https://health.severance.healthcare/health/encyclopedia/disease/body_board.do'
        self.base_url = 'https://health.severance.healthcare/health/encyclopedia/disease/body_board.do?mode=list&srBodyCategoryId=1385'
    
    def get_crawled_data(self):
        # 브라우저를 띄우지 않는 옵션
        options = webdriver.ChromeOptions()
        options.add_argument("headless")
        driver = webdriver.Chrome(options=options)

        disease_urls = []
        data = []

        # driver로 목록 페이지를 스크롤해서 모든 질병의 상세페이지 카드를 로드
        driver.get(self.base_url)
        driver.implicitly_wait(2)
        load_btn = driver.find_element(By.CSS_SELECTOR, '#btnMoreArticle')
        is_load_btn_invisible = load_btn.get_attribute("style")
        while not is_load_btn_invisible:
            load_btn.click()
            time.sleep(1)
            load_btn = driver.find_element(By.CSS_SELECTOR, '#btnMoreArticle')
            is_load_btn_invisible = driver.find_element(By.CSS_SELECTOR, '#btnMoreArticle').get_attribute("style")
        
        # 모든 카드가 로드된 html 소스를 파싱해서 상세페이지 링크 가져오기
        disease_cards = driver.find_elements(By.CSS_SELECTOR, 'div.thumb-item > a')
        for card in disease_cards:
            disease_urls.append(card.get_attribute('href'))
        
        # 각 페이지에서 정보 뽑아내기
        for url in tqdm(disease_urls):
            driver.get(url)
            driver.implicitly_wait(3)

            disease_name = driver.find_element(By.CSS_SELECTOR, 'h3.subject').text
            disease_detail = driver.find_element(By.CSS_SELECTOR, 'div.article-body').text
            metadata = {'name': disease_name,
                        'source': url}
            disease = {'content': disease_detail, 'metadata': metadata}
            data.append(disease)

        driver.quit()
        return data
