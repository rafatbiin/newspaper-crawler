# -*- coding: utf-8 -*-
"""
Tests for the ProthomAlo spider.

Unit tests verify spider logic with mock responses.
Live tests hit prothomalo.com to check whether the spider still works against
the current site — failures there indicate the site has changed and the spider
needs updating.
"""

import json
import unittest
from datetime import timezone
from scrapy.http import HtmlResponse, TextResponse, Request
from crawler.spiders.prothomalo import ProthomaloSpider


def make_html_response(url, html):
    """Helper to create a fake Scrapy HtmlResponse."""
    request = Request(url=url)
    return HtmlResponse(url=url, body=html.encode('utf-8'), request=request)


def make_api_response(data):
    """Helper to create a fake Scrapy TextResponse for API JSON."""
    url = 'https://www.prothomalo.com/api/v1/stories?limit=50&offset=0'
    request = Request(url=url)
    return TextResponse(
        url=url,
        body=json.dumps(data).encode('utf-8'),
        encoding='utf-8',
        request=request,
    )


SAMPLE_STORY = {
    'url': 'https://www.prothomalo.com/bangladesh/63pv7s72ir',
    'slug': 'bangladesh/63pv7s72ir',
    'headline': 'Sample headline',
    'published-at': 1_700_000_000_000,   # Unix ms
    'first-published-at': 1_700_000_000_000,
    'last-published-at': 1_700_000_000_000,
    'author-name': 'Test Author',
    'story-template': 'text',
    'sections': [{'slug': 'bangladesh', 'name': 'বাংলাদেশ'}],
    'metadata': {},
}


class TestProthomaloSpiderUnit(unittest.TestCase):

    def setUp(self):
        self.spider = ProthomaloSpider()

    # ------------------------------------------------------------------ #
    # Metadata
    # ------------------------------------------------------------------ #

    def test_spider_metadata(self):
        """Spider should have correct name and allowed domains."""
        self.assertEqual(self.spider.name, 'prothomalo')
        self.assertIn('prothomalo.com', self.spider.allowed_domains)

    def test_start_requests_hits_api(self):
        """start_requests should yield a request to the stories API."""
        requests = list(self.spider.start_requests())
        self.assertEqual(len(requests), 1)
        self.assertIn('/api/v1/stories', requests[0].url)
        self.assertIn('offset=0', requests[0].url)

    # ------------------------------------------------------------------ #
    # parse_api — discovery and date extraction
    # ------------------------------------------------------------------ #

    def test_parse_api_yields_article_request(self):
        """parse_api should yield a Request for each story URL."""
        response = make_api_response({'stories': [SAMPLE_STORY]})
        results = list(self.spider.parse_api(response, offset=0))
        article_requests = [r for r in results if isinstance(r, Request)
                            and 'api/v1' not in r.url]
        self.assertEqual(len(article_requests), 1)
        self.assertEqual(article_requests[0].url, SAMPLE_STORY['url'])

    def test_parse_api_sets_publish_date_from_timestamp(self):
        """parse_api should convert the ms timestamp to a UTC datetime."""
        response = make_api_response({'stories': [SAMPLE_STORY]})
        results = list(self.spider.parse_api(response, offset=0))
        article_request = next(r for r in results
                               if isinstance(r, Request) and 'api/v1' not in r.url)
        publish_date = article_request.cb_kwargs['publish_date']
        self.assertIsNotNone(publish_date)
        self.assertEqual(publish_date.tzinfo, timezone.utc)
        # 1_700_000_000_000 ms → 2023-11-14
        self.assertEqual(publish_date.year, 2023)

    def test_parse_api_skips_story_without_url(self):
        """parse_api should skip stories that have no url field."""
        story_no_url = {k: v for k, v in SAMPLE_STORY.items() if k != 'url'}
        response = make_api_response({'stories': [story_no_url]})
        results = list(self.spider.parse_api(response, offset=0))
        article_requests = [r for r in results if isinstance(r, Request)
                            and 'api/v1' not in r.url]
        self.assertEqual(len(article_requests), 0)

    def test_parse_api_paginates_when_full_page(self):
        """parse_api should yield the next-page API request when a full page returns."""
        stories = [dict(SAMPLE_STORY, url=f'https://www.prothomalo.com/bd/{i}')
                   for i in range(self.spider.PAGE_SIZE)]
        response = make_api_response({'stories': stories})
        results = list(self.spider.parse_api(response, offset=0))
        next_page_requests = [r for r in results if isinstance(r, Request)
                              and 'api/v1' in r.url]
        self.assertEqual(len(next_page_requests), 1)
        self.assertIn(f'offset={self.spider.PAGE_SIZE}', next_page_requests[0].url)

    def test_parse_api_no_pagination_on_partial_page(self):
        """parse_api should NOT yield a next-page request when fewer than PAGE_SIZE stories return."""
        response = make_api_response({'stories': [SAMPLE_STORY]})
        results = list(self.spider.parse_api(response, offset=0))
        next_page_requests = [r for r in results if isinstance(r, Request)
                              and 'api/v1' in r.url]
        self.assertEqual(len(next_page_requests), 0)

    # ------------------------------------------------------------------ #
    # parse_article — HTML capture
    # ------------------------------------------------------------------ #

    def test_parse_article_sets_url_language_html(self):
        """parse_article should set url, language, and html on the item."""
        url = 'https://www.prothomalo.com/bangladesh/63pv7s72ir'
        html = '<html><body><p>Article text</p></body></html>'
        response = make_html_response(url, html)
        from datetime import datetime
        publish_date = datetime(2023, 11, 14, tzinfo=timezone.utc)

        items = list(self.spider.parse_article(response, publish_date=publish_date))
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item['url'], url)
        self.assertEqual(item['language'], 'bn')
        self.assertIn(b'Article text', item['html'])

    def test_parse_article_uses_api_date(self):
        """parse_article should use the publish_date passed from parse_api."""
        from datetime import datetime
        url = 'https://www.prothomalo.com/bangladesh/63pv7s72ir'
        html = '<html><body></body></html>'
        response = make_html_response(url, html)
        expected = datetime(2023, 11, 14, tzinfo=timezone.utc)

        item = list(self.spider.parse_article(response, publish_date=expected))[0]
        self.assertEqual(item['publish_date'], expected)

    def test_parse_article_falls_back_to_jsonld_date(self):
        """parse_article should extract datePublished from JSON-LD when API date is missing."""
        url = 'https://www.prothomalo.com/bangladesh/63pv7s72ir'
        html = '''<html><head>
            <script type="application/ld+json">
                {"@type": "NewsArticle", "datePublished": "2024-01-15T10:00:00+06:00"}
            </script>
        </head><body></body></html>'''
        response = make_html_response(url, html)

        item = list(self.spider.parse_article(response, publish_date=None))[0]
        self.assertIsNotNone(item['publish_date'])
        self.assertEqual(item['publish_date'].year, 2024)
        self.assertEqual(item['publish_date'].month, 1)
        self.assertEqual(item['publish_date'].day, 15)

    def test_parse_article_date_is_none_when_no_source(self):
        """parse_article should not crash when both API date and JSON-LD are absent."""
        url = 'https://www.prothomalo.com/bangladesh/63pv7s72ir'
        html = '<html><body><p>No date anywhere.</p></body></html>'
        response = make_html_response(url, html)

        item = list(self.spider.parse_article(response, publish_date=None))[0]
        self.assertIsNone(item['publish_date'])


class TestProthomaloLive(unittest.TestCase):
    """
    Live integration tests that hit prothomalo.com to verify whether the spider
    still works against the current site.

    A PASS means the spider is compatible; a FAIL means the site has changed
    and the spider needs updating.  Tests are skipped if the site is unreachable.
    """

    BASE_URL = 'https://www.prothomalo.com/'
    API_URL = 'https://www.prothomalo.com/api/v1/stories?limit=5'

    def _fetch(self, url, timeout=15):
        import requests
        try:
            response = requests.get(url, timeout=timeout, headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            })
            return response
        except Exception as e:
            self.skipTest(f'Cannot reach {url}: {e}')

    def test_live_homepage_reachable(self):
        """prothomalo.com homepage should return HTTP 200."""
        response = self._fetch(self.BASE_URL)
        self.assertEqual(response.status_code, 200,
                         f'Expected 200 but got {response.status_code}')

    def test_live_api_returns_stories(self):
        """The stories API should return at least one story."""
        response = self._fetch(self.API_URL)
        self.assertEqual(response.status_code, 200,
                         f'API returned {response.status_code}')
        data = response.json()
        stories = data.get('stories', [])
        self.assertGreater(len(stories), 0, 'API returned zero stories')

    def test_live_api_story_has_valid_url_and_timestamp(self):
        """Each API story should have a url and a valid Unix ms timestamp."""
        response = self._fetch(self.API_URL)
        stories = response.json().get('stories', [])
        if not stories:
            self.skipTest('API returned no stories')
        story = stories[0]
        self.assertIn('url', story, 'Story missing "url" field')
        self.assertIn('prothomalo.com', story['url'])
        published_ms = story.get('published-at')
        self.assertIsNotNone(published_ms, 'Story missing "published-at" field')
        # Sanity-check: timestamp should be after 2010 (> 1.26 trillion ms)
        self.assertGreater(published_ms, 1_260_000_000_000,
                           f'Timestamp {published_ms} looks invalid')

    def test_live_article_jsonld_has_date(self):
        """A fetched article page should contain a JSON-LD block with datePublished."""
        api_resp = self._fetch(self.API_URL)
        stories = api_resp.json().get('stories', [])
        if not stories:
            self.skipTest('API returned no stories')

        article_url = stories[0].get('url')
        response = self._fetch(article_url)
        self.assertIn('datePublished', response.text,
                      f'No datePublished found in JSON-LD on {article_url}')


if __name__ == '__main__':
    unittest.main(verbosity=2)
