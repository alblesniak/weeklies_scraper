import scrapy
from scrapy.loader import ItemLoader
from weeklies_scraper.items import WeekliesScraperItem
from urllib.parse import urljoin

# Spider for crawling Przewodnik Katolicki magazine's website


class PrzewodnikKatolickiSpider(scrapy.Spider):
    # Set the name of the spider
    name = "przewodnik_katolicki"
    # Set the list of allowed domains that this spider is allowed to crawl
    allowed_domains = ["przewodnik-katolicki.pl"]
    # Set the start_urls of the spider
    start_urls = ["https://www.przewodnik-katolicki.pl/Archiwum?rok=wszystkie"]

    def parse(self, response):
        self.logger.info(
            "Parse function called parse on {}".format(response.url))
        # Parse the response and yield new requests to crawl other pages
        years = response.xpath(
            "//div[@class='rok-wydania clearfix']/ul/li[not(contains(@class, 'wszystkie'))]/a/@href"
        )
        for year in years:
            data_dict = {
                'issue_name': 'Przewodnik Katolicki',
                'issue_year': int(year.get().split('/')[-1])
            }
            # Yield a request and parse next page
            yield response.follow(year, callback=self.parse_issues, meta=data_dict)

    def parse_issues(self, response):
        self.logger.info(
            "Parse function called parse_issues on {}".format(response.url))
        data_dict = response.meta
        lis = response.xpath("//ul[@class='lista-artykulow']/li")
        for li in lis:
            issue_url = li.xpath(".//div[@class='zdjecie']/a/@href").get()
            issue_cover_url = urljoin(response.url, li.xpath(
                '//div[@class="zdjecie"]/a/img/@src').get()).replace(".aspx?width=150", ".aspx?width=600")
            issue_number = li.xpath(
                ".//h3[@class='naglowek-0']/a/text()").re_first(r"\d{1,2}(?=[/-])")
            if issue_number is not None:
                data_dict["issue_cover_url"] = issue_cover_url
                data_dict["issue_number"] = int(issue_number)
                # Yield a request and parse next page
                yield response.follow(issue_url, callback=self.parse_issue, meta=data_dict)

    def parse_issue(self, response):
        self.logger.info(
            "Parse function called parse_issue on {}".format(response.url))
        # Extract data from the issue page
        sections = response.xpath(
            "//div[@class='spis-tresci']/ul/li[@class='sekcja']")
        for section in sections:
            section_name = section.xpath(".//h3/a/text()").get()
            articles = section.xpath(
                "//div[@class='artykuly-sekcji']/ul/li[@class='zajawka-art']"
            )
            for article in articles:
                if not article.xpath("//h3[contains(@class, 'klodka')]"):
                    article_url = article.xpath(".//h3/a/@href").get()
                    article_title = article.xpath(".//h3/a/text()").get()
                    data_dict = response.meta
                    data_dict["issue_url"] = response.url
                    data_dict["article_title"] = article_title
                    data_dict["section_name"] = section_name
                    # Yield a request to crawl the article page, passing along the issue data as metadata
                    yield response.follow(
                        article_url, callback=self.parse_article, meta=data_dict
                    )

    def parse_article(self, response):
        self.logger.info(
            "Parse function called parse_article on {}".format(response.url)
        )
        article_authors = response.xpath(
            "//article[@class='artykul']//span[@class='wpis']//text()").get()
        article_intro = response.xpath("//p[@class='wstep']/text()").get()
        article_content = response.xpath(
            "//article[@class='artykul']/div[@class='tresc']/descendant-or-self::text()[not(parent::style)]"
        ).extract()
        article_tags = response.xpath(
            ".//div[@class='tagi clearfix']/ul/li/span/a/text()"
        ).extract()
        # Create a ItemLoader object to load the article information
        loader = ItemLoader(item=WeekliesScraperItem(), response=response)
        # Add the information about the issue to the loader
        loader.add_value("issue_name", response.meta["issue_name"])
        loader.add_value("issue_number", response.meta["issue_number"])
        loader.add_value("issue_year", int(response.meta["issue_year"]))
        loader.add_value("issue_url", response.meta["issue_url"])
        loader.add_value("issue_cover_url", response.meta["issue_cover_url"])
        # Add the section name to the loader
        loader.add_value("section_name", response.meta["section_name"])
        # Add the article authors to the loader
        loader.add_value("article_authors", article_authors)
        loader.add_value("article_url", response.url)
        # Extract the article title and add it to the loader
        loader.add_value("article_title", response.meta["article_title"])
        # Extract the article intro and add it to the loader
        loader.add_value("article_intro", article_intro)
        # Extract the article content and add it to the loader
        loader.add_value("article_content", article_content)
        # Extract the article tags and add it to the loader
        loader.add_value("article_tags", '; '.join(article_tags))
        # Load the item with the extracted information
        yield loader.load_item()
