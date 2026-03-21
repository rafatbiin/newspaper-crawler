import json
from datetime import datetime, timezone
from scrapy import Spider, Request
from crawler.items.news import News


class ProthomaloSpider(Spider):

    name = 'prothomalo'
    allowed_domains = ['prothomalo.com']
    API_URL = 'https://www.prothomalo.com/api/v1/stories'
    PAGE_SIZE = 50

    def start_requests(self):
        yield Request(
            f'{self.API_URL}?limit={self.PAGE_SIZE}&offset=0',
            callback=self.parse_api,
            cb_kwargs={'offset': 0},
        )

    def parse_api(self, response, offset):
        stories = response.json().get('stories', [])

        for story in stories:
            url = story.get('url')
            if not url:
                continue
            published_ms = story.get('published-at')
            publish_date = (
                datetime.fromtimestamp(published_ms / 1000, tz=timezone.utc)
                if published_ms else None
            )
            yield Request(
                url,
                callback=self.parse_article,
                cb_kwargs={'publish_date': publish_date},
            )

        if len(stories) == self.PAGE_SIZE:
            next_offset = offset + self.PAGE_SIZE
            yield Request(
                f'{self.API_URL}?limit={self.PAGE_SIZE}&offset={next_offset}',
                callback=self.parse_api,
                cb_kwargs={'offset': next_offset},
            )

    def parse_article(self, response, publish_date=None):
        news = News()
        news['url'] = response.url
        news['html'] = response.body
        news['language'] = 'bn'
        news['publish_date'] = publish_date or self._date_from_jsonld(response)
        yield news

    def _date_from_jsonld(self, response):
        for raw in response.css('script[type="application/ld+json"]::text').getall():
            try:
                data = json.loads(raw)
                date_str = data.get('datePublished')
                if date_str:
                    import dateparser
                    return dateparser.parse(date_str)
            except (ValueError, TypeError):
                continue
        return None
