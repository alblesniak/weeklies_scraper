import random
from scrapy import signals
from scrapy import settings
from scrapy.downloadermiddlewares.httpproxy import HttpProxyMiddleware
from scrapy.exceptions import IgnoreRequest
# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter


class RandomProxy(HttpProxyMiddleware):
    """
    A middleware that randomly selects a proxy from a list of proxies
    and sets it for each request.
    """

    def __init__(self, auth_encoding='latin-1'):
        """
        Initialize the middleware with the specified encoding for the
        HTTP basic auth credentials in the proxy.
        """
        super(RandomProxy, self).__init__(auth_encoding)
        # Load the list of proxies from a file
        with open(settings['PROXY_SERVERS_FILE'], 'r') as f:
            self.proxies = [line.strip() for line in f]
        # Set the threshold for the number of failures
        # after which a proxy is removed from the list
        self.fail_threshold = 3
        # Keep track of the number of failures for each proxy
        self.fail_counts = {}

    def process_request(self, request, spider):
        """
        Set a random proxy for the request.
        """
        request.meta['proxy'] = random.choice(self.proxies)
        # Initialize the failure count for the proxy
        self.fail_counts[request.meta['proxy']] = 0

    def process_response(self, request, response, spider):
        """
        Handle the response for the request.
        If the response status is greater than or equal to 400,
        increment the failure count for the proxy and remove it
        from the list if the number of failures exceeds the threshold.
        """
        if response.status >= 400:
            self.fail_counts[request.meta['proxy']] += 1
            if self.fail_counts[request.meta['proxy']] >= self.fail_threshold:
                self.proxies.remove(request.meta['proxy'])
            raise IgnoreRequest
        return response


class WeekliesScraperSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class WeekliesScraperDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)
