import re
import os
import time
import scrapy
import undetected_chromedriver as uc
from lxml import html
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from weeklies_scraper.items import WeekliesScraperItem
from scrapy.loader import ItemLoader


class NewsweekSpider(scrapy.Spider):
    name = 'newsweek'
    allowed_domains = ['newsweek.pl']
    start_urls = ['https://accounts.google.com/o/oauth2/v2/auth/oauthchooseaccount?redirect_uri=https%3A%2F%2Fkonto.onet.pl%2Fnewapi%2Ffederation%2Fauth-google&state=eyJzdGF0ZSI6Ii9saXN0YS13eWRhbiIsImNsaWVudF9pZCI6Im5ld3N3ZWVrLnBsLm9rb250by5mcm9udC5vbmV0YXBpLnBsIiwicmVkaXJlY3RfdXJpIjoiaHR0cHM6Ly93d3cubmV3c3dlZWsucGwvcGF5d2FsbC9va29udG8vYXV0aCIsImJhY2tQYWdlUGF0aCI6InNpZ25pbiIsImxvY2FsZSI6InBsIiwicHJvdmlkZXIiOiJnb29nbGUuY29tIn0%3D&scope=email&client_id=426231693590-uhijhfb26n5t8pl01e7teje0sl6389ra.apps.googleusercontent.com&provider=google.com&response_type=code&service=lso&o2v=2&flowName=GeneralOAuthFlow']

    def __init__(self):
        self.driver = uc.Chrome()
        self.username = os.environ.get('POLITYKA_SCRAPER_LOGIN')
        self.password = os.environ.get('POLITYKA_SCRAPER_PASSWORD')

    def login(self, response):
        self.logger.info("Login into website...")
        self.driver.get(response.url)

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
        for year in range(2014, 2023):
            yield response.follow(f'https://www.newsweek.pl/lista-wydan//{str(year)}', callback=self.parse_issues)

    def parse_issues(self, response):
        self.logger.info(
            'Parse function called parse_issues on {}'.format(response.url))
        self.driver.get(response.url)
        root = html.fromstring(self.driver.page_source)
        time.sleep(1)
        issues = root.xpath(
            '//div[@class="editionList__elementWrapper"]/a[@class="editionsList__element "]/@href')
        for issue in issues:
            issue_url = urljoin('https://www.newsweek.pl/', issue)
            yield response.follow(issue_url, callback=self.parse_issue)

    def parse_issue(self, response):
        self.logger.info(
            'Parse function called parse_issue on {}'.format(response.url))
        self.driver.get(response.url)
        root = html.fromstring(self.driver.page_source)

        try:
            issue_name_number = root.xpath(
                '(//h2[@class="pwEditionList__title pwEditionList__title--standard"]/text())[1]')[0].strip()
            match = re.match(r'(.*) (\d{1,2})\/(\d{4})', issue_name_number)
            data_dict = {
                'issue_name': match.group(1),
                'issue_number': match.group(2),
                'issue_year': match.group(3),
                'issue_url': response.url,
                'issue_cover_url': root.xpath(
                    '//div[@class="pwEdition__current"]//img/@data-original')
            }
        except Exception as e:
            if response.url == 'https://www.newsweek.pl/nwpl_2021_01_20210104':
                data_dict = {
                    'issue_name': 'Newsweek Polska',
                    'issue_number': '1',
                    'issue_year': '2021',
                    'issue_url': response.url,
                    'issue_cover_url': root.xpath(
                        '//div[@class="pwEdition__current"]//img/@data-original')
                }
            elif response.url == 'https://www.newsweek.pl/nwws_2021003_20211020':
                data_dict = {
                    'issue_name': 'Newsweek Extra',
                    'issue_number': '3',
                    'issue_year': '2021',
                    'issue_url': response.url,
                    'issue_cover_url': root.xpath(
                        '//div[@class="pwEdition__current"]//img/@data-original')
                }
            elif response.url == 'https://www.newsweek.pl/nwws_202003_20200819':
                data_dict = {
                    'issue_name': 'Newsweek Extra',
                    'issue_number': '3',
                    'issue_year': '2020',
                    'issue_url': response.url,
                    'issue_cover_url': root.xpath(
                        '//div[@class="pwEdition__current"]//img/@data-original')
                }
            elif response.url == 'https://www.newsweek.pl/nwws_202005_20201112':
                data_dict = {
                    'issue_name': 'Newsweek Extra',
                    'issue_number': '5',
                    'issue_year': '2020',
                    'issue_url': response.url,
                    'issue_cover_url': root.xpath(
                        '//div[@class="pwEdition__current"]//img/@data-original')
                }
            elif response.url == 'https://www.newsweek.pl/nwws_202004_20201021':
                data_dict = {
                    'issue_name': 'Newsweek Extra',
                    'issue_number': '4',
                    'issue_year': '2020',
                    'issue_url': response.url,
                    'issue_cover_url': root.xpath(
                        '//div[@class="pwEdition__current"]//img/@data-original')
                }
            elif response.url == 'https://www.newsweek.pl/nwpsyws_2022001_20220608':
                data_dict = {
                    'issue_name': 'Newsweek Psychologia',
                    'issue_number': '1',
                    'issue_year': '2022',
                    'issue_url': response.url,
                    'issue_cover_url': root.xpath(
                        '//div[@class="pwEdition__current"]//img/@data-original')
                }
            elif response.url == 'https://www.newsweek.pl/nwpsyws_2022002_20220831':
                data_dict = {
                    'issue_name': 'Newsweek Psychologia',
                    'issue_number': '2',
                    'issue_year': '2022',
                    'issue_url': response.url,
                    'issue_cover_url': root.xpath(
                        '//div[@class="pwEdition__current"]//img/@data-original')
                }
            elif response.url == 'https://www.newsweek.pl/nwws_2022003_20220928':
                data_dict = {
                    'issue_name': 'Newsweek Extra',
                    'issue_number': '3',
                    'issue_year': '2022',
                    'issue_url': response.url,
                    'issue_cover_url': root.xpath(
                        '//div[@class="pwEdition__current"]//img/@data-original')
                }
            else:
                with open('error.txt', 'a') as f:
                    f.write(f'{response.url} {e}\n')

        editorial_url = root.xpath(
            '//h2[@class="pwEditionList__title pwEditionList__title--intro"]/following-sibling::div/a/@href')
        if editorial_url:
            data_dict['section_name'] = 'Po prostu'
            yield response.follow(editorial_url[0], callback=self.parse_article, meta=data_dict)

        sections = root.xpath(
            './/div[@class="pwEditionList__wrapper"]')
        for section in sections:
            section_name = section.xpath('./h2/text()')[0].strip()
            data_dict['section_name'] = section_name
            sections_urls = section.xpath(
                './/a[contains(@class, "pwArt")]/@href')
            for section_url in sections_urls:
                yield response.follow(section_url, callback=self.parse_article, meta=data_dict)

    def parse_article(self, response):
        self.logger.info(
            'Parse function called parse_article on {}'.format(response.url))
        self.driver.get(response.url)
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        article_content = []
        divs = soup.find_all(
            "div", class_=["ringBlockType-paragraph", "ringBlockType-heading"])
        for div in divs:
            element = div.find(['p', 'h2', 'h3'])
            if element != None:
                article_content.append(element.get_text().strip())
        root = html.fromstring(self.driver.page_source)
        data_dict = response.meta
        try:
            data_dict['article_title'] = root.xpath(
                '//h1[@data-cy="detail-title"]/span/text()')[0].strip()
        except:
            # data_dict['article_title'] = root.xpath(
            #     '//h1[@data-cy="detail-title"]/span/text()')
            print(root.xpath(
                '//h1[@data-cy="detail-title"]/span/text()'), type(root.xpath(
                    '//h1[@data-cy="detail-title"]/span/text()')))
        data_dict['article_authors'] = ', '.join(root.xpath(
            './/a[@data-cy="detail-author-name"]/text() | .//span[@data-cy="detail-author-name"]/text()')).strip()
        data_dict['article_intro'] = root.xpath('//div[@id="lead"]/p/text()')
        data_dict['article_tags'] = '; '.join([tag.strip() for tag in root.xpath(
            '//div[@data-section="detail-tags"]/ul/li/a/text()')])
        data_dict['article_url'] = response.url
        loader = ItemLoader(item=WeekliesScraperItem(), response=response)
        loader.add_value('issue_name', data_dict['issue_name'])
        loader.add_value('issue_number', data_dict['issue_number'])
        loader.add_value('issue_year', int(data_dict['issue_year']))
        loader.add_value('issue_url', data_dict['issue_url'])
        loader.add_value('issue_cover_url', data_dict['issue_cover_url'])
        loader.add_value(
            'article_title', data_dict['article_title'])
        loader.add_value('article_intro', data_dict['article_intro'])
        loader.add_value('article_content', '\n'.join(article_content))
        loader.add_value('article_authors',
                         data_dict['article_authors'])
        loader.add_value('article_tags', data_dict['article_tags'])
        loader.add_value('section_name', data_dict['section_name'])
        loader.add_value('article_url', data_dict['article_url'])
        yield loader.load_item()


# Check before running:
# https://www.newsweek.pl/innowacje-paul-de-courtois-z-bmw-o-przyszlosci-motoryzacji/5e0we2l (trzeba dodać h3)
