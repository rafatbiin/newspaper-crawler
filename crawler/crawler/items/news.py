import scrapy


class News(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()

    url = scrapy.Field()
    md5 = scrapy.Field()
    title = scrapy.Field()
    publish_date = scrapy.Field()
    text = scrapy.Field()
    html = scrapy.Field()
    videos = scrapy.Field()
    domain = scrapy.Field()
    tags = scrapy.Field()
    top_image = scrapy.Field()
    images = scrapy.Field()
    language = scrapy.Field()