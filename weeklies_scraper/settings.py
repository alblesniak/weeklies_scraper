import os

BOT_NAME = "weeklies_scraper"

# List of modules where the spider is located
SPIDER_MODULES = ["weeklies_scraper.spiders"]

# Module where the spider is located
NEWSPIDER_MODULE = "weeklies_scraper.spiders"

# User agent for the spider to use
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36"

# Set to True to enable the spider to respect the website's robots.txt file
ROBOTSTXT_OBEY = False

# Middlewares to use for the spider
SPIDER_MIDDLEWARES = {
    "weeklies_scraper.middlewares.WeekliesScraperSpiderMiddleware": 543,
}

# Middlewares to use for the downloader
DOWNLOADER_MIDDLEWARES = {
    "weeklies_scraper.middlewares.WeekliesScraperDownloaderMiddleware": 543,
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 544,
    'weeklies_scraper.middlewares.RandomProxy': 545,
}

# Pipelines to use for the spider

ITEM_PIPELINES = {
    "weeklies_scraper.pipelines.ScriptStripperPipeline": 200,
    "weeklies_scraper.pipelines.TextCleanerPipeline": 300,
    "weeklies_scraper.pipelines.SQLitePipeline": 400
}

# Connection string for the database
CONNECTION_STRING = "sqlite:///scrapy_data.db"

# List of HTTP status codes that the spider is allowed to handle
HTTPERROR_ALLOWED_CODES = [404]

# Set the request fingerprinter implementation to a future-proof version
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
# Set the twisted reactor to a future-proof version
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# Set the log level for the spider
LOG_LEVEL = "INFO"

#  Set the log file for the spider
# LOG_FILE = "scrapy.log"

# Set path to the Google Cloud Platform settings for proxy servers
# See: https://www.youtube.com/watch?v=0MZY649MiQM&t
GCLOUD_CONFIG_FILE = "gcloud_proxies_config.json"

# Set path to file with proxy servers
PROXY_SERVERS_FILE = "proxy_servers.txt"

# Set open port for proxy servers
PROXY_PORT = "3128"

# Set credentials to proxy servers
PROXY_LOGIN = os.environ.get('PROXY_LOGIN')
PROXY_PASSWORD = os.environ.get('PROXY_PASSWORD')
