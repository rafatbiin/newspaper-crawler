import gzip
from crawler.utils.url_processor import URLProcessor
from crawler.utils.newspaper.newspaper import Article


class NewsDetailsExtractorPipeline(object):

    def process_item(self, item, spider):
        article = self.get_article(item['url'], item['html'], item['language'])
        item['title'] = article.title
        item['text'] = article.text
        item['html'] = gzip.compress(item['html'])
        item['videos'] = list(article.movies)
        item['domain'] = URLProcessor.get_domain(item['url'])
        item['top_image'] = article.top_image
        item['images'] = list(article.images)
        item['md5'] = URLProcessor.get_md5(item['url'])
        item['tags'] = self.get_tags(article, spider)

        return item

    def get_article(self, url, html, language):
        article = Article(url, language=language)
        article.download(input_html=html)
        article.parse()
        return article

    def get_tags(self, article, spider):
        if len(article.tags) == 0:
            return None
        if spider.name != "prothomalo":
            return None
        return list(article.tags)