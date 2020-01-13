import datetime as dt
from scrapy import spiderloader
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor

settings = get_project_settings()
spider_loader = spiderloader.SpiderLoader.from_settings(settings)
spiders = spider_loader.list()
classes = [spider_loader.load(name) for name in spiders]


def crawl_job():
    """
    Job to start spiders.
    Return Deferred, which will execute after crawl has completed.
    """
    runner = CrawlerRunner(settings)
    for spider_name in classes:
        runner.crawl(spider_name)
    return runner.join()


def schedule_next_crawl(null, hour, minute):
    tomorrow = (
            dt.datetime.now() + dt.timedelta(days=1)
    ).replace(hour=hour, minute=minute, second=0, microsecond=0)
    sleep_time = (tomorrow - dt.datetime.now()).total_seconds()
    reactor.callLater(sleep_time, crawl)


def crawl():
    d = crawl_job()
    # crawl everyday at 12:02
    d.addCallback(schedule_next_crawl, hour=0, minute=2)


def catch_error(failure):
    print(failure.value)


if __name__ == "__main__":
    crawl()
    reactor.run()
