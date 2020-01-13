from datetime import timedelta

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from crawler.items.news import News
import dateparser


class TheDailyStarSpider(CrawlSpider):
    name = 'thedailystar'
    allowed_domains = ['thedailystar.net']
    start_urls = ['https://www.thedailystar.net/']
    rules = (
        Rule(LinkExtractor(allow='-(\d)+$', deny='\/bangla'), callback='parse_article'),
        Rule(LinkExtractor(allow=()))
    )

    def parse_article(self, response):
        news = News()
        news["url"] = response.url
        news["html"] = response.body
        news["language"] = 'en'
        news['publish_date'] = self.get_publish_date(response)
        yield news

    def get_publish_date(self, response):
        publish_date = response.css(".small-text meta:nth-child(1)::attr(content)").extract_first()
        if publish_date is None:
            publish_date = response.css(".author span::text").extract_first()

        if publish_date is not None:
            publish_date = dateparser.parse(publish_date) + timedelta(hours=6)
        return publish_date
