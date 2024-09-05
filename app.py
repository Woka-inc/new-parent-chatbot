from data_processor import process_healthychildren_articles, json_loader
from crawler import scrape_conditions

condition_url = 'https://www.healthychildren.org/English/health-issues/conditions/'
base_url = 'https://www.healthychildren.org'
original_article_path = './res/scraped_condition_articles.json'
cleaned_article_path = './res/articles.json'

if __name__ == "__main__":
    # 데이터 수집, 전처리
    scrape_conditions(base_url, condition_url, path_to_save=original_article_path)
    process_healthychildren_articles(original_article_path, cleaned_article_path)

    # 참고자료(JSON) Document list로 로드
    documents = json_loader(cleaned_article_path)