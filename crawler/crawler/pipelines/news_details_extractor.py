import base64
import gzip
from crawler.utils.url_processor import URLProcessor
from crawler.utils.newspaper.newspaper import Article


class NewsDetailsExtractorPipeline(object):

    def process_item(self, item, spider):
        article = self.get_article(item['url'], item['html'], item['language'])
        item['title'] = article.title
        item['text'] = article.text
        item['videos'] = list(article.movies)
        item['domain'] = URLProcessor.get_domain(item['url'])
        item['top_image'] = article.top_image
        item['images'] = list(article.images)
        item['md5'] = URLProcessor.get_md5(item['url'])
        self.get_tags(article, item, spider)

        item.pop('html', None)
        return item

    def get_article(self, url, html, language):
        article = Article(url, language=language)
        article.download(input_html=html)
        article.parse()
        return article

    def get_tags(self, article, item, spider):
        if len(article.tags) == 0:
            return
        if spider.name != "prothomalo":
            return
        item['tags'] = list(article.tags)
