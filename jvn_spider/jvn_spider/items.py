# jvn_spider/items.py

import scrapy

class JvnItem(scrapy.Item):
    jvndb_id = scrapy.Field()
    title = scrapy.Field()
    description = scrapy.Field()
    technologies = scrapy.Field()
    # version = scrapy.Field()
