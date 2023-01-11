import re
import os
import time
import scrapy
from lxml import html
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from weeklies_scraper.items import WeekliesScraperItem
from urllib.parse import urljoin
from scrapy.loader import ItemLoader


class WprostSpider(scrapy.Spider):
    name = 'wprost'
    allowed_domains = ['wprost.pl']
    start_urls = ['https://www.wprost.pl/tygodnik/archiwum']

    def __init__(self):
        chrome_options = Options()
        # chrome_options.add_argument("--disable-extensions")
        # chrome_options.add_argument("--disable-gpu")
        # chrome_options.add_argument("--no-sandbox")
        # chrome_options.add_argument('--window-size=1420,1080')
        # chrome_options.add_argument("--headless")
        # chrome_options.add_argument("--accept_untrusted_certs")
        # chrome_options.add_argument("--accept_insecure_certs")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.username = os.environ.get('WEEKLIES_SCRAPER_LOGIN')
        self.password = os.environ.get('WEEKLIES_SCRAPER_PASSWORD')

    def login(self, response):
        self.driver.get(response.url)
        username_element = self.driver.find_element(
            "xpath", '//input[@id="username"]')
        self.driver.execute_script(
            "document.getElementById('username').click()")
        self.driver.execute_script(
            "arguments[0].setAttribute('value', '" + self.username + "')", username_element)
        time.sleep(1)
        password_element = self.driver.find_element(
            "xpath", '//input[@id="password"]')
        self.driver.execute_script(
            "document.getElementById('password').click()")
        self.driver.execute_script(
            "arguments[0].setAttribute('value', '" + self.password + "')", password_element)
        self.driver.execute_script("arguments[0].click();", password_element)
        time.sleep(1)
        button_element = self.driver.find_element(
            "xpath", '//button[@class="button button-action"]')
        self.driver.execute_script("arguments[0].click();", button_element)
        self.logger.info("Login to the website...")
        time.sleep(1)
        # Store the cookies set by the website
        self.cookies = self.driver.get_cookies()

    def check_login(self, root):
        try:
            profil_element = root.xpath(
                "//span[@id='header-user-button']/@title")[0]
            self.logger.info(f"You are logged in as {profil_element}")
            return profil_element
        except:
            self.logger.info(f"Waiting for webpage to be loaded...")

    def parse(self, response):
        self.logger.info(
            'Parse function called parse_issue on {}'.format(response.url))

        # Log in to the website before making any requests
        self.login(response=response)
        root = html.fromstring(self.driver.page_source)
        # Check if login succeded
        if self.check_login(root=root):
            years = root.xpath('.//ul[@class="years mtop10"]/li/a/@href')
            for year in years:
                year_url = urljoin(response.url, year)
                yield response.follow(year_url, callback=self.parse_year)
        else:
            self.logger.error(f'Could not to login to {response.url}')

    def parse_year(self, response):
        self.logger.info(
            'Parse function called parse_issue on {}'.format(response.url))
        self.driver.get(response.url)
        root = html.fromstring(self.driver.page_source)
        issues = root.xpath(
            './/div[@class="wrapper"]/ul[not(@class)]/li[@class="item disabled-select"]/a/@href')
        for issue in issues:
            issue_url = urljoin(response.url, issue)
            yield response.follow(issue_url, callback=self.parse_issue)

    def parse_issue(self, response):
        self.logger.info(
            'Parse function called parse_issue on {}'.format(response.url))
        self.driver.get(response.url)
        time.sleep(1)
        root = html.fromstring(self.driver.page_source)
        issue_number = re.search(r"\d{1,2}/\d{4}", root.xpath(
            './/div[@class="wrapper"]/h2/span/text()')[0]).group(0).split('/')
        issue_dict = {
            'issue_name': 'Wprost',
            'issue_number': f'{issue_number[0].zfill(2)}',
            'issue_year': issue_number[1],
            'issue_url': response.url,
            'issue_cover_url': root.xpath('//a[@class="cover"]/img/@src')[0]
        }
        articles = root.xpath(
            './/ul[@id="main-list"]/li[@class="item"]/a[@class="title"]/@href')
        for article in articles:
            article_url = urljoin(response.url, article)
            yield response.follow(article_url, callback=self.parse_article, meta=issue_dict)

    def parse_article(self, response):
        self.logger.info(
            'Parse function called parse_article on {}'.format(response.url))
        time.sleep(1)
        root = html.fromstring(self.driver.page_source)
        # Check if login succeded
        if self.check_login(root=root):
            loader = ItemLoader(item=WeekliesScraperItem(), response=response)
            loader.add_value('issue_name', response.meta['issue_name'])
            loader.add_value('issue_number', response.meta['issue_number'])
            loader.add_value('issue_year', response.meta['issue_year'])
            loader.add_value('issue_url', response.meta['issue_url'])
            loader.add_value('issue_cover_url',
                             response.meta['issue_cover_url'])
            loader.add_value('article_authors', ', '.join(root.xpath(
                '//article[@class="article"]/ul[@class="art-authors"]/li/a[@rel="author"]/strong/text()')))
            loader.add_value('article_title', root.xpath(
                '//h1[@class="art-title" or @class="art-title art-title-large"]/span/text()'))
            loader.add_value('article_intro', root.xpath(
                '//div[@id="art-lead-inner"]/text()'))
            loader.add_value('article_content', root.xpath(
                '//div[@id="art-text-inner"]//text()[not(ancestor::*[@class="art-text-frame"])]'))
            loader.add_value('article_url', response.url)
            yield loader.load_item()
        else:
            self.logger.error(f'Could not to login to {response.url}')
            # Log in to the website before making any requests
            self.login(response=response)
            time.sleep(3)
            yield response.follow(response.url, callback=self.parse_article, meta=response.meta, cookies=self.cookies)

        # https://www.wprost.pl/tygodnik/10059385/Rzadowe-trzesienie-ziemi.html
