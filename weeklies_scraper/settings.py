import os

BOT_NAME = "weeklies_scraper"

# List of modules where the spider is located
SPIDER_MODULES = ["weeklies_scraper.spiders"]

# Module where the spider is located
NEWSPIDER_MODULE = "weeklies_scraper.spiders"

# User agent for the spider to use
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36"

# Enable the AutoThrottle extension
AUTOTHROTTLE_ENABLED = True

# The initial download delay
AUTOTHROTTLE_START_DELAY = 0.5

# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 60

# The average number of requests Scrapy should be sending in parallel to
# each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# Enable showing throttling stats for every response received:
AUTOTHROTTLE_DEBUG = False

# Set to True to enable the spider to respect the website's robots.txt file
ROBOTSTXT_OBEY = False

# Middlewares to use for the spider
SPIDER_MIDDLEWARES = {
    # "weeklies_scraper.middlewares.WeekliesScraperSpiderMiddleware": 543,
}

# Middlewares to use for the downloader
DOWNLOADER_MIDDLEWARES = {
    "weeklies_scraper.middlewares.ExistenceCheckMiddleware": 543,
    # 'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
    # 'rotating_proxies.middlewares.BanDetectionMiddleware': 620,
}

# Pipelines to use for the spider

ITEM_PIPELINES = {
    "weeklies_scraper.pipelines.FullfillDataPipeline": 100,
    "weeklies_scraper.pipelines.ScriptStripperPipeline": 200,
    "weeklies_scraper.pipelines.TextCleanerPipeline": 300,
    "weeklies_scraper.pipelines.ShortestPipeline": 400,
    "weeklies_scraper.pipelines.SQLitePipeline": 500
}

# Connection string for the database
CONNECTION_STRING = "sqlite:///scrapy_data.db"

# List of HTTP status codes that the spider is allowed to handle
# HTTPERROR_ALLOWED_CODES = [404]

# Set the request fingerprinter implementation to a future-proof version
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'
# Set the twisted reactor to a future-proof version
# TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# Set the log level for the spider
# LOG_LEVEL = "ERROR"

#  Set the log file for the spider
# LOG_FILE = "scrapy.log"

# Set path to file with proxy servers
ROTATING_PROXY_LIST_PATH = os.path.abspath("proxy_servers.txt")
