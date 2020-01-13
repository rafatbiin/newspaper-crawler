from datetime import timedelta

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from crawler.items.news import News
import dateparser


class Bdnews24Spider(CrawlSpider):

    name = 'bdnews24'
    allowed_domains = ['bangla.bdnews24.com']
    start_urls = ['https://bangla.bdnews24.com/']
    rules = (
        Rule(LinkExtractor(allow='article(\d)+'), callback='parse_article'),
        Rule(LinkExtractor(allow=()))
    )

    def parse_article(self, response):
        news = News()
        news["url"] = response.url
        news["html"] = response.body
        news["language"] = 'bn'
        news['publish_date'] = dateparser.parse(
            response.css("#article_notations span:nth-child(2)::text").extract_first()) + timedelta(hours=2)
        yield news
