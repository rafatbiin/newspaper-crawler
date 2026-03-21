# -*- coding: utf-8 -*-
"""
Tests for the ProthomAlo spider.

Unit tests verify spider logic with mock responses.
Live tests hit prothomalo.com to check whether the spider still works against
the current site — failures there indicate the site has changed and the spider
needs updating.
"""

import unittest
from scrapy.http import HtmlResponse, Request
from crawler.spiders.prothomalo import ProthomaloSpider


def make_response(url, html):
    """Helper to create a fake Scrapy HtmlResponse."""
    request = Request(url=url)
    return HtmlResponse(url=url, body=html.encode('utf-8'), request=request)


class TestProthomaloSpiderUnit(unittest.TestCase):

    def setUp(self):
        self.spider = ProthomaloSpider()

    def test_spider_metadata(self):
        """Spider should have correct name, allowed domains, and start URL."""
        self.assertEqual(self.spider.name, 'prothomalo')
        self.assertIn('prothomalo.com', self.spider.allowed_domains)
        self.assertIn('https://www.prothomalo.com/', self.spider.start_urls)

    def test_parse_article_url_and_language(self):
        """parse_article should set url and language='bn' correctly."""
        url = 'https://www.prothomalo.com/bangladesh/article/12345/test'
        html = '<html><body><div class="time"><span>January 1, 2024</span></div></body></html>'
        response = make_response(url, html)

        results = list(self.spider.parse_article(response))

        self.assertEqual(len(results), 1)
        item = results[0]
        self.assertEqual(item['url'], url)
        self.assertEqual(item['language'], 'bn')

    def test_parse_article_html_body_captured(self):
        """parse_article should capture the raw HTML body."""
        url = 'https://www.prothomalo.com/bangladesh/article/12345/test'
        # Include a valid date so dateparser does not receive None
        html = '<html><body><div class="time"><span>January 1, 2024</span></div><p>Article content</p></body></html>'
        response = make_response(url, html)

        item = list(self.spider.parse_article(response))[0]

        self.assertIsNotNone(item['html'])
        self.assertIn(b'Article content', item['html'])

    def test_parse_article_publish_date_extracted(self):
        """parse_article should extract publish date from .time span:nth-child(1)."""
        url = 'https://www.prothomalo.com/bangladesh/article/12345/test'
        html = '''
        <html><body>
            <div class="time"><span>January 15, 2024</span></div>
        </body></html>
        '''
        response = make_response(url, html)

        item = list(self.spider.parse_article(response))[0]

        self.assertIsNotNone(item['publish_date'])
        self.assertEqual(item['publish_date'].year, 2024)
        self.assertEqual(item['publish_date'].month, 1)
        self.assertEqual(item['publish_date'].day, 15)

    def test_parse_article_missing_date_crashes_spider(self):
        """
        BUG: parse_article crashes with TypeError when the date CSS selector
        returns nothing (None).  dateparser >= 1.0.0 raises TypeError for None
        input, whereas the project originally pinned dateparser==0.7.6 which
        handled None gracefully.  This test documents the bug.
        """
        url = 'https://www.prothomalo.com/bangladesh/article/99999/no-date'
        html = '<html><body><article><h1>No date article</h1></article></body></html>'
        response = make_response(url, html)

        with self.assertRaises(TypeError):
            list(self.spider.parse_article(response))

    def test_link_extraction_pattern_matches_numeric_article_urls(self):
        """Spider rules should match the original article/<digits> URL format."""
        from scrapy.linkextractors import LinkExtractor
        le = LinkExtractor(allow=r'article\/(\d)+')

        url = 'https://www.prothomalo.com/'
        html = '''
        <html><body>
            <a href="/bangladesh/article/12345/some-article">Article 1</a>
            <a href="/category/sports">Category (should NOT match)</a>
            <a href="/article/67890/another">Article 2</a>
        </body></html>
        '''
        response = make_response(url, html)
        link_urls = [link.url for link in le.extract_links(response)]

        self.assertTrue(any('article/12345' in u for u in link_urls))
        self.assertTrue(any('article/67890' in u for u in link_urls))
        self.assertFalse(any('/category/sports' in u for u in link_urls))


class TestProthomaloLive(unittest.TestCase):
    """
    Live integration tests that hit prothomalo.com to verify whether the spider
    still works against the current site.

    A PASS means the spider is compatible; a FAIL means the site has changed
    and the spider needs updating.  Tests are skipped if the site is unreachable.
    """

    BASE_URL = 'https://www.prothomalo.com/'

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

    def test_live_article_links_found_on_homepage(self):
        """
        EXPECTED FAILURE — site structure changed.

        The spider looks for links matching 'article/<digits>' but prothomalo.com
        now uses alphanumeric slugs (e.g. /bangladesh/capital/95434wz3jz).
        No 'article/<digits>' links appear in the page source, so the spider
        will find zero articles on every crawl.
        """
        import re
        response = self._fetch(self.BASE_URL)

        old_pattern_links = re.findall(
            r'href=["\'][^"\']*article/\d+[^"\']*["\']', response.text
        )
        new_pattern_links = re.findall(
            r'https?://www\.prothomalo\.com/[a-z\-]+/[a-z\-]+/[a-z0-9]{8,}',
            response.text.replace('\\u002F', '/')
        )

        self.assertGreater(
            len(old_pattern_links), 0,
            'BROKEN: No article/<digits> links found on homepage.\n'
            f'Site now uses alphanumeric slug URLs instead '
            f'(e.g. /bangladesh/capital/95434wz3jz).\n'
            f'New-style slugs found: {len(new_pattern_links)}.\n'
            'The spider URL pattern needs updating.'
        )

    def test_live_article_date_selector(self):
        """
        EXPECTED FAILURE — date CSS selector broken.

        The spider uses '.time span:nth-child(1)' to extract the publish date,
        but this selector returns nothing on current article pages.  The site
        likely switched to client-side rendering (React/Next.js), so date
        information is no longer present in the static HTML.
        """
        import re
        homepage = self._fetch(self.BASE_URL)

        # Attempt to find any article URL (old or new format)
        old_links = re.findall(
            r'href=["\']([^"\']*article/\d+[^"\']*)["\']', homepage.text
        )
        new_links = re.findall(
            r'(https?://www\.prothomalo\.com/[a-z\-]+/[a-z\-]+/[a-z0-9]{8,})',
            homepage.text.replace('\\u002F', '/')
        )

        article_url = None
        if old_links:
            path = old_links[0]
            article_url = ('https://www.prothomalo.com' + path
                           if path.startswith('/') else path)
        elif new_links:
            article_url = new_links[0]
        else:
            self.skipTest('No article links of any format found on homepage.')

        article_response = self._fetch(article_url)
        scrapy_response = HtmlResponse(
            url=article_url,
            body=article_response.content,
            request=Request(url=article_url)
        )

        date_text = scrapy_response.css('.time span:nth-child(1)::text').extract_first()
        self.assertIsNotNone(
            date_text,
            f'BROKEN: CSS selector ".time span:nth-child(1)" returned nothing '
            f'on {article_url}.\n'
            'The site no longer embeds the date in static HTML '
            '(likely moved to client-side rendering).\n'
            'The spider date extraction logic needs updating.'
        )


if __name__ == '__main__':
    unittest.main(verbosity=2)
