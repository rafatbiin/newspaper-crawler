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
    'scrapyelasticsearch.scrapyelasticsearch.ElasticSearchPipeline': 300
}

ELASTICSEARCH_SERVERS = [os.environ.get('ELASTICSEARCH_SERVERS') if os.environ.get('ELASTICSEARCH_SERVERS') is not None \
                             else 'http://localhost:9200']
ELASTICSEARCH_INDEX = 'newspaper_data'
ELASTICSEARCH_INDEX_DATE_FORMAT = '%Y-%m-%d'
ELASTICSEARCH_TYPE = 'news'
ELASTICSEARCH_UNIQ_KEY = 'md5'  # Custom unique key
ELASTICSEARCH_BUFFER_LENGTH = 50

AUTOTHROTTLE_ENABLED = True
