# -*- coding: utf-8 -*-

import logging
from logging.handlers import RotatingFileHandler
import os

from scrapy.utils.log import configure_logging

LOG_ENABLED = False
# Disable default Scrapy log settings.
configure_logging(install_root_handler=False)

# Define your logging settings.
log_file = './tmp/news_log.log'

os.makedirs(os.path.dirname(log_file), exist_ok=True)


root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
rotating_file_log = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=1)
rotating_file_log.setLevel(logging.INFO)
rotating_file_log.setFormatter(formatter)
root_logger.addHandler(rotating_file_log)


BOT_NAME = 'newspaper-crawler'

SPIDER_MODULES = ['crawler.spiders']
NEWSPIDER_MODULE = 'crawler.spiders'


# mongo db configuration
MONGODB_HOST = os.environ.get('MONGODB_HOST') if os.environ.get('MONGODB_HOST') is not None else 'localhost'
MONGODB_PORT = int(os.environ.get('MONGODB_PORT')) if os.environ.get('MONGODB_PORT') is not None else 9116
MONGODB_NAME = 'newspaper_data'

LOG_LEVEL = 'INFO'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# set depth limit for crawler
DEPTH_LIMIT = int(os.environ.get('CRAWL_DEPTH')) if os.environ.get('CRAWL_DEPTH') is not None else 2

# add download delay for network issue
DOWNLOAD_DELAY = 4

ITEM_PIPELINES = {
    'crawler.pipelines.news_details_extractor.NewsDetailsExtractorPipeline': 200,
    'crawler.pipelines.mongodb.MongoPipeline': 300,
}

AUTOTHROTTLE_ENABLED = True
