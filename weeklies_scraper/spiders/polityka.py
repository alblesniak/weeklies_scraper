import re
import os
import time
import scrapy
import undetected_chromedriver as uc
from lxml import html
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from weeklies_scraper.items import WeekliesScraperItem
from scrapy.loader import ItemLoader


class PolitykaSpider(scrapy.Spider):
    name = 'polityka'
    allowed_domains = ['polityka.pl']
    start_urls = ['https://accounts.google.com/o/oauth2/v2/auth/oauthchooseaccount?scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.email&access_type=online&include_granted_scopes=true&response_type=code&redirect_uri=https%3A%2F%2Fwww.polityka.pl%2Fsso%2Flogin%2Foauth2%2Fgoogle&state=%7B%22login_success%22%3A%22https%3A%2F%2Fwww.polityka.pl%2Farchiwumpolityki%3F_spring_security_remember_me%3Dtrue%22%2C%22login_error%22%3A%22https%3A%2F%2Fwww.polityka.pl%2Flogowanie%3FloginSuccessUrl%3Dhttps%253A%252F%252Fwww.polityka.pl%252Farchiwumpolityki%253F_spring_security_remember_me%253Dtrue%22%7D&client_id=1007415323808-ofsln7k3obli7mh1fqi5icgvmlvlncn3.apps.googleusercontent.com&service=lso&o2v=2&flowName=GeneralOAuthFlow']

    def __init__(self):
        self.driver = uc.Chrome()
        self.username = os.environ.get('POLITYKA_SCRAPER_LOGIN')
        self.password = os.environ.get('POLITYKA_SCRAPER_PASSWORD')

    def parse(self, response):
        self.logger.info(
            'Parse function called parse_issue on {}'.format(response.url))
        self.driver.get(response.url)
        time.sleep(1)
        WebDriverWait(self.driver, 30).until(EC.visibility_of_element_located(
            (By.NAME, 'identifier'))).send_keys(f'{self.username}\n')
        time.sleep(1)
        WebDriverWait(self.driver, 30).until(EC.visibility_of_element_located(
            (By.NAME, 'password'))).send_keys(f'{self.password}\n')
        time.sleep(1)
        self.driver.get(response.url)
        root = html.fromstring(self.driver.page_source)
        issues = root.xpath(
            './/div[@class="cg_toc_covers_list_wrapper"]/ul/li')
        for issue in issues:
            issue_number_year = issue.xpath(
                './/div[@class ="cg_toc_covers_dates"]/div[@class ="cg_toc_covers_no_edition"]/text()')[0].split('.')
            data_dict = {
                'issue_name': 'Polityka',
                'issue_url': issue.xpath('.//a/@href')[0],
                'issue_number': issue_number_year[0].strip(),
                'issue_year': issue_number_year[1].strip(),
                'issue_cover_url': f'''http:{issue.xpath('.//div[@class = "cg_toc_covers_popup_full"]/div[@class = "cg_toc_popup_img"]/img/@x-data-src')[0].strip()}'''
            }
            yield response.follow(data_dict['issue_url'], callback=self.parse_issue, meta=data_dict)
        # Parse rest issues
        magazines_dict = {
            'Polityka Niezbędnik Inteligenta': 'https://www.polityka.pl/niezbednik/numery/',
            'Polityka Pomocnik Historyczny': 'https://www.polityka.pl/pomocnikhistoryczny/numery/',
            'Polityka Poradnik Psychologiczny': 'https://www.polityka.pl/jamyoni/numery/',
            'Polityka Salon': 'https://www.polityka.pl/salon/numery/'
        }
        for issue_name, issues_url in magazines_dict.items():
            yield response.follow(issues_url, callback=self.parse_rest_issues, meta={'issue_name': issue_name})

    def parse_rest_issues(self, response):
        self.logger.info(
            'Parse function called parse_rest_issues on {}'.format(response.url))
        self.driver.get(response.url)
        root = html.fromstring(self.driver.page_source)
        issues_urls = root.xpath('//div[@class="cg_toc_covers_links"]/a/@href')
        issues_dates = [element.strip() for element in root.xpath(
            '//div[@class="cg_toc_covers_dates"]/div[@class="cg_toc_covers_date_edition"]/text()')]
        issues_cover_urls = [f'http::{i}' for i in root.xpath(
            './/div[@class="cg_toc_covers_img"]/img/@x-data-src')]
        dates_urls_mapped = list(
            zip(issues_dates, issues_urls, issues_cover_urls))
        numbers_urls_list = self.sort_magazines(dates_urls_mapped)
        for issue_number_year, issue_url, issue_cover_url in numbers_urls_list:
            data_dict = {
                'issue_name': response.meta['issue_name'],
                'issue_url': issue_url,
                'issue_number': issue_number_year.split('/')[0],
                'issue_year': issue_number_year.split('/')[1],
                'issue_cover_url': issue_cover_url
            }
            yield response.follow(issue_url, callback=self.parse_issue, meta=data_dict)

    def sort_magazines(self, magazines_list):
        # Sort the list by date
        magazines_sorted = sorted(
            magazines_list, key=lambda x: datetime.strptime(x[0], '%d.%m.%Y'))
        # Create a dictionary that will store information about how many numbers from a given year we have added
        counts_by_year = {}
        # Initialize the result list
        result = []
        # Iterate over the sorted list
        for date, url, cover in magazines_sorted:
            # Get the year from the date
            year = datetime.strptime(date, '%d.%m.%Y').year
            # If we do not have information about this year in the dictionary, add it with the number 1
            if year not in counts_by_year:
                counts_by_year[year] = 1
            # Otherwise, increase the number by 1
            else:
                counts_by_year[year] += 1
            # Add the tuple to the result list
            result.append((f"{counts_by_year[year]}/{year}", url, cover))
        # Return the result
        return result

    def parse_issue(self, response):
        self.logger.info(
            'Parse function called parse_issue on {}'.format(response.url))
        self.driver.get(response.url)
        time.sleep(1)
        print(response.meta['issue_url'])
        root = html.fromstring(self.driver.page_source)
        articles_urls = root.xpath(
            '(//div[@class="cg_toc_leading_article "]/a/@href | //div[@class="cg_toc_leading_comment "]/a/@href | //section[@class="cg_toc_sec_list   "]//ul[@class="cg_toc_sec_list_articles"]/li/div/a/@href)')
        for article_url in articles_urls:
            yield response.follow(article_url, callback=self.parse_article, meta=response.meta)

    def parse_article(self, response):
        self.logger.info(
            'Parse function called parse_article on {}'.format(response.url))
        self.driver.get(response.url)
        data_dict = response.meta
        root = html.fromstring(self.driver.page_source)
        article_url = response.url
        section_name = root.xpath(
            '//div[@class="cg_article_section"]/a/text()')[0].strip()
        article_title = root.xpath(
            '//h1[@class="cg_article_internet_title"]/text()')[0].strip()
        article_author = root.xpath(
            '//div[@class="cg_article_author_name"]/text()')[0].strip()
        article_intro = root.xpath(
            '//div[@class="cg_article_lead"]//text()')[0].strip()
        article_content = root.xpath(
            '//div[@class="cg_article_meat"]/p//text()')
        article_tags = root.xpath('.//ul[@class="cg_article_tags"]/li//text()')
        loader = ItemLoader(item=WeekliesScraperItem(), response=response)
        loader.add_value('issue_name', data_dict['issue_name'])
        loader.add_value('issue_url', data_dict['issue_url'])
        loader.add_value('issue_number', data_dict['issue_number'])
        loader.add_value('issue_year', int(data_dict['issue_year']))
        loader.add_value('issue_cover_url', data_dict['issue_cover_url'])
        loader.add_value('section_name', section_name)
        loader.add_value('article_url', article_url)
        loader.add_value('article_authors', article_author)
        loader.add_value('article_title', article_title)
        loader.add_value('article_intro', article_intro)
        loader.add_value('article_content', article_content)
        loader.add_value('article_tags', article_tags)
        yield loader.load_item()

# (//div[@class="cg_toc_leading_article "] | //div[@class="cg_toc_leading_comment "] | //section[@class="cg_toc_sec_list   "])//ul[@class="cg_toc_sec_list_articles"]/li/div/a/@href
