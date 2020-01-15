# Newspaper Crawler
Scrapy based crawler which crawls newspaper.

### Required Dependencies:
  1. docker
  2. docker-compose

### Run the Crawler from source:
- First clone the repository. as it contains [newspaper3k](https://github.com/rafatbiin/newspaper) as a submodule of this repository,follow:

```bash
$ git clone --recurse-submodules https://github.com/rafatbiin/newspaper-crawler.git
```

- Open terminal inside of the project folder.
 
- checkout to [elasticsearch_pipeline](https://github.com/rafatbiin/newspaper-crawler/tree/elasticsearch_pipeline) branch.

- run the docker-compose file:

```bash
$ docker-compose up -d
```

- your elasticsearch server should be live at ``` localhost:9200 ```

### Configuration
- The logs will be saved in a directory called **tmp** inside the [runner](https://github.com/rafatbiin/newspaper-crawler/tree/master/crawler/crawler/runner) package.
- The default crawling depth is set to 2. If you need to change that, you'll find the **CRAWL_DEPTH** environment variable inside the [docker-compose.yml](https://github.com/rafatbiin/newspaper-crawler/blob/master/docker-compose.yml) file.


## About the Newspaper3k library

It's an awesome library which helps parsing data from a news article.At this moment, it doesn't have Bengali language support. So I tweaked the library to add Bengali language support. I've already created a [Pull Request](https://github.com/codelucas/newspaper/pull/764) for adding Bengali language support to the library.


##  Development
You are welcome to contribute in this project. You can:
- create new issues pointing out the bugs.
- add new newspaper sources.
- add new features to extend the project.


### Supported sources
| Available Sources                      | Can Crawl  |
| -------------------------------------- | :--------: |
| https://www.prothomalo.com/            |      ✔     |
| https://bangla.bdnews24.com/           |      ✔     |
| https://www.thedailystar.net/          |      ✔     |