import scrapy
from scrapy.crawler import CrawlerProcess


class MyAsyncSpider1(scrapy.spiders.AsyncSpider):
    name = "myasyncspider1"
    start_urls = ["http://www.example.com/page1"]

    async def parse(self, response):
        # parse the response and yield new requests to crawl other pages
        yield scrapy.Request(url="http://www.example.com/page2", callback=self.parse)


class MyAsyncSpider2(scrapy.spiders.AsyncSpider):
    name = "myasyncspider2"
    start_urls = ["http://www.example.com/page3"]

    async def parse(self, response):
        # parse the response and yield new requests to crawl other pages
        yield scrapy.Request(url="http://www.example.com/page4", callback=self.parse)


# create a CrawlerProcess with 4 concurrent spiders
process = CrawlerProcess(settings={"CONCURRENT_SPIDERS": 4})
process.crawl(MyAsyncSpider1)
process.crawl(MyAsyncSpider2)
process.start()
