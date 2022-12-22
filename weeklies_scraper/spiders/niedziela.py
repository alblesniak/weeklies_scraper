import scrapy
from scrapy.loader import ItemLoader
from weeklies_scraper.items import WeekliesScraperItem


# Spider for crawling Niedziela magazine's website
class NiedzielaSpider(scrapy.Spider):
    # Set the name of the spider
    name = "niedziela"
    # Set the list of allowed domains that this spider is allowed to crawl
    allowed_domains = ["niedziela.pl"]
    # Set the start_urls of the spider
    start_urls = ["https://m.niedziela.pl/archiwum"]

    def parse(self, response):
        self.logger.info(
            "Parse function called parse on {}".format(response.url))
        # Print the proxy IP
        proxy_ip = response.meta['proxy']
        print(f'Proxy IP: {proxy_ip}')
        # Parse the response and yield new requests to crawl other pages
        years = response.xpath(
            './/ul[@class="list-inline pt-main px-main text-center"]/li/a/@href'
        )
        for year in years:
            data_dict = {
                'issue_name': 'Niedziela',
                'issue_year': int(year.get().split('/')[-1])
            }
            # Yield a request and parse next page
            yield response.follow(year, callback=self.parse_issues, meta=data_dict)

    def parse_issues(self, response):
        self.logger.info(
            "Parse function called parse_issues on {}".format(response.url)
        )
        divs = response.xpath(
            "//div[@class='col-6 col-xs-3 px-half mb-main text-center']"
        )
        for div in divs:
            issue_url = div.xpath("./a[@class]/@href").get()
            issue_cover_url = div.xpath(
                '//img[@class="border-solid img-fluid"]/@src').get()
            data_dict = response.meta
            data_dict["issue_cover_url"] = issue_cover_url
            data_dict["issue_url"] = issue_url
            # Yield a request and parse next page
            yield response.follow(issue_url, callback=self.parse_issue, meta=data_dict)

    def parse_issue(self, response):
        self.logger.info(
            "Parse function called parse_issue on {}".format(response.url))
        # Extract data from the issue page
        issue_number = response.xpath(
            '//h1[@class="title-page mx-main mb-main text-center mt-main"]/text()').re_first(r"\d{1,2}(?=[/-])")
        data_dict = response.meta
        data_dict["issue_number"] = int(issue_number)
        data_dict["issue_url"] = response.url
        sections = response.xpath(
            "//div[h5[@class='text-center text-uppercase color-logo-darker mt-2x']]"
        )
        for section in sections:
            data_dict["section_name"] = section.xpath("./h5/text()").get()
            articles = section.xpath(".//a/@href")
            for article in articles:
                # Yield a request to crawl the article page, passing along the issue data as metadata
                yield response.follow(
                    article, callback=self.parse_article, meta=data_dict
                )

    def parse_article(self, response):
        self.logger.info(
            "Parse function called parse_article on {}".format(response.url)
        )
        # Check if the article is not a paid content
        if not response.xpath(
            '//div[@class="row my-2x label-color"]//p[@class="py-half px-main" and contains(text(),"Pełna treść tego i pozostałych artykułów")]'
        ):
            # Create a ItemLoader object to load the article information
            loader = ItemLoader(item=WeekliesScraperItem(), response=response)
            # Add the information about the issue to the loader
            loader.add_value("issue_name", response.meta["issue_name"])
            loader.add_value("issue_number", response.meta["issue_number"])
            loader.add_value("issue_year", int(response.meta["issue_year"]))
            loader.add_value("issue_url", response.meta["issue_url"])
            loader.add_value("issue_cover_url",
                             response.meta["issue_cover_url"])
            # Add the section name to the loader
            loader.add_value("section_name", response.meta["section_name"])
            # Add the article URL to the loader
            loader.add_value("article_url", response.url)
            # Extract the article title and add it to the loader
            loader.add_xpath(
                "article_title", "(//h1[contains(@class, 'title-page')])[1]/text()"
            )
            # Extract the article intro and add it to the loader
            article_intro = response.xpath(
                "(//p[contains(@class, 'article-lead')])[1]/text()"
            ).extract()
            if article_intro is not None:
                loader.add_value("article_intro", article_intro)
            else:
                loader.add_value("article_intro", "")
            # Extract the article content and add it to the loader
            article_content = response.xpath(
                "//article[@class='article  mx-main']/p[not(@*[name() != 'class']) or @class='styt' or @class='pyt' or @class='odp']/text()"
            ).extract()
            if article_content is not None:
                loader.add_value("article_content", article_content)
            else:
                loader.add_value("article_content", "")
            # Extract the article authors and add it to the loader
            article_authors = response.xpath(
                "(//h3/text()[preceding-sibling::i])[1]"
            ).extract()
            if article_authors is not None:
                loader.add_value("article_authors", article_authors)
            else:
                loader.add_value("article_authors", "")
            # Extract the article tags and add it to the loader
            article_tags = response.xpath(
                "//p[contains(., '[ TEMATY ]')]/following-sibling::ul/li/a/text()"
            ).extract()
            if article_tags is not None:
                loader.add_value("article_tags", article_tags)
            else:
                loader.add_value("article_tags", "")
            # Load the item with the extracted information
            print(loader.load_item())
            yield loader.load_item()
