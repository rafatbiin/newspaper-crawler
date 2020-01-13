import pymongo
from crawler.items.news import News
from scrapy.exceptions import DropItem


class MongoPipeline(object):

    def __init__(self, mongo_host, mongo_port, mongo_db_name):

        self.mongo_host = mongo_host
        self.mongo_port = mongo_port
        self.mongo_db_name = mongo_db_name

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_host=crawler.settings.get('MONGODB_HOST'),
            mongo_port=crawler.settings.get('MONGODB_PORT'),
            mongo_db_name=crawler.settings.get('MONGODB_NAME')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_host, self.mongo_port)
        self.db = self.client[self.mongo_db_name]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        if isinstance(item, News):
            if self.db['news_article'].count({'url': item['url']}) > 0:
                raise DropItem("Item already exists")
            else:
                self.db['news_article'].insert(dict(item))

        return item
