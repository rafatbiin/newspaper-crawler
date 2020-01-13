from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from crawler.items.news import News
import dateparser


class ProthomaloSpider(CrawlSpider):

    name = 'prothomalo'
    allowed_domains = ['prothomalo.com']
    start_urls = ['https://www.prothomalo.com/']
    rules = (
        Rule(LinkExtractor(allow='article\/(\d)+'), callback='parse_article'),
        Rule(LinkExtractor(allow=()))
    )

    def parse_article(self, response):
        news = News()
        news["url"] = response.url
        news["html"] = response.body
        news["language"] = 'bn'
        news['publish_date'] = dateparser.parse(response.css(".time span:nth-child(1)::text").extract_first())
        yield news
