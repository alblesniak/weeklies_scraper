# -*- coding: utf-8 -*-
import re
from scrapy import Spider
from scrapy.loader import ItemLoader
from urllib.parse import urljoin
from weeklies_scraper.items import WeekliesScraperItem


class GoscNiedzielnySpider(Spider):
    name = 'gosc_niedzielny'
    allowed_domains = ['gosc.pl']
    start_urls = ['https://www.gosc.pl/wyszukaj/wydania/3.Gosc-Niedzielny']

    def parse(self, response):
        self.logger.info(
            'Parse function called parse on {}'.format(response.url))
        years = response.xpath(
            '//ul[@class="list list-full list-years list-years-full"]/li/a/@href')
        for year in years:
            yield response.follow(year, callback=self.parse_issues)

    def parse_issues(self, response):
        self.logger.info(
            'Parse function called parse_issues on {}'.format(response.url))
        issues = response.xpath(
            '//div[@class="search-result release-result"]//a[@class="i"]/@href')
        data_dict = {}
        for issue in issues:
            issue_url = issue.get()
            if issue_url.count('/') == 4:
                stripped_url = issue_url[:]
            else:
                stripped_url, _ = issue_url.rsplit('/', 1)
            data_dict['issue_url'] = urljoin(
                'https://www.gosc.pl', stripped_url)
            yield response.follow(issue_url, callback=self.parse_issue, meta=data_dict)
            yield response.follow(issue_url.replace('/przeglad/', '/wszystko/'), callback=self.parse_issue, meta=data_dict)
        next_page = response.xpath(
            '//a[@class="pgr_arrow" and contains(text(), "›")]/@href').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse_issues)

    def parse_issue(self, response):
        self.logger.info(
            'Parse function called parse_issue on {}'.format(response.url))
        issue_number = response.xpath(
            '//span[@class="product-name"]/parent::a/text()').re_first(r"\d{1,2}/\d{4}").split('/')
        data_dict = response.meta
        data_dict['issue_name'] = 'Gość Niedzielny'
        data_dict['issue_number'] = f"{issue_number[0].zfill(2)}"
        data_dict['issue_year'] = issue_number[1]
        data_dict['issue_cover_url'] = urljoin('https:', response.xpath(
            '//div[contains(@class, "fl-w100 release")]//img/@src[1]').get().replace('.webp', ''))
        sections = response.xpath(
            './/div[@class="source-result source-result-source-preview"]')
        if len(sections) > 0:
            for section in sections:
                section_name = section.xpath('.//h4/a/text()').get()
                articles = section.xpath(
                    './/div[@class="search-result"]//h1[@class="src_auth_h"]/a/@href')
                data_dict['section_name'] = section_name
                for article in articles:
                    data_dict['article_content'] = []
                    yield response.follow(article, callback=self.parse_article, meta=data_dict)
        else:
            articles = response.xpath(
                '//div[@class="search-result"]//h1[@class="src_auth_h"]/a/@href').getall()
            for article in articles:
                data_dict['article_content'] = []
                data_dict['section_name'] = ""
                yield response.follow(article, callback=self.parse_article, meta=data_dict)
            next_page = response.xpath(
                '//a[@class="pgr_arrow" and contains(text(), "›")]/@href').get()
            if next_page:
                yield response.follow(next_page, callback=self.parse_issue, meta=data_dict)

    def parse_article(self, response):
        self.logger.info(
            'Parse function called parse_article on {}'.format(response.url))
        acrobat = response.xpath(
            '//div[@class="txt__lead"]/p[contains(text(), "Plik do pobrania w wersji (pdf)")]')
        limiter = response.xpath('//p[@class="limiter"]')

        if not acrobat and not limiter:
            data_dict = response.meta
            if len(data_dict['article_content']) == 0:
                data_dict['article_url'] = response.url
                data_dict['article_authors'] = response.xpath(
                    './/p[@class="l doc-author"]/b//text()')
                data_dict['article_title'] = response.xpath(
                    '//div[contains(@class, "cf txt ")]/h1//text()')
                data_dict['article_intro'] = response.xpath(
                    '//div[@class="txt__lead"]//p//text()')
                page_content = response.xpath(
                    './/div[@class="txt__content"]/div[@class=" txt__rich-area"]//text()').extract()
                for p in page_content:
                    data_dict['article_content'].append(p)
                next_page = response.xpath(
                    '//div[@class="pgr"]/span[@class="pgr_nrs"]/span/following-sibling::a[1]/@href').get()
                if next_page:
                    yield response.follow(next_page, callback=self.parse_article, meta=data_dict)
                else:
                    loader = ItemLoader(
                        item=WeekliesScraperItem(), response=response)
                    loader.add_value('issue_name', data_dict['issue_name'])
                    loader.add_value(
                        'issue_number', data_dict['issue_number'])
                    loader.add_value('issue_year', data_dict['issue_year'])
                    loader.add_value('issue_url', data_dict['issue_url'])
                    loader.add_value('issue_cover_url',
                                     data_dict['issue_cover_url'])
                    loader.add_value(
                        'section_name', data_dict['section_name'])
                    loader.add_value('article_url', data_dict['article_url'])
                    loader.add_value('article_authors',
                                     data_dict['article_authors'].extract())
                    loader.add_value(
                        'article_title', data_dict['article_title'].get())
                    loader.add_value(
                        'article_intro', data_dict['article_intro'].get())
                    loader.add_value('article_content',
                                     '\n'.join(data_dict['article_content']))
                    yield loader.load_item()
            else:
                page_content = response.xpath(
                    './/div[@class="txt__content"]/div[@class=" txt__rich-area"]/p').extract()
                for p in page_content:
                    data_dict['article_content'].append(p)
                next_page = response.xpath(
                    '//div[@class="pgr"]/span[@class="pgr_nrs"]/span/following-sibling::a[1]/@href').get()
                if next_page:
                    yield response.follow(next_page, callback=self.parse_article, meta=data_dict)
                else:
                    loader = ItemLoader(
                        item=WeekliesScraperItem(), response=response)
                    loader.add_value('issue_name', data_dict['issue_name'])
                    loader.add_value(
                        'issue_number', data_dict['issue_number'])
                    loader.add_value(
                        'issue_year', data_dict['issue_year'])
                    loader.add_value('issue_url', data_dict['issue_url'])
                    loader.add_value('issue_cover_url',
                                     data_dict['issue_cover_url'])
                    loader.add_value(
                        'section_name', data_dict['section_name'])
                    loader.add_value('article_url', data_dict['article_url'])
                    loader.add_value('article_authors',
                                     data_dict['article_authors'].extract())
                    loader.add_value(
                        'article_title', data_dict['article_title'].get())
                    loader.add_value(
                        'article_intro', data_dict['article_intro'].get())
                    loader.add_value('article_tags', None)
                    loader.add_value('article_content',
                                     '\n'.join(data_dict['article_content']))
                    yield loader.load_item()
