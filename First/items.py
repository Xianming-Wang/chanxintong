# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class FirstItem(scrapy.Item):
    task_name = scrapy.Field()
    title = scrapy.Field()
    content_url = scrapy.Field()
    publish_date = scrapy.Field()

    pure_content = scrapy.Field()
    html_content = scrapy.Field()
    origin_source = scrapy.Field()
    origin_author = scrapy.Field()
    title_in_content = scrapy.Field()
    update_date = scrapy.Field()

    column = scrapy.Field()
    origin_deptment = scrapy.Field()
    origin_place = scrapy.Field()
    origin_type = scrapy.Field()
    industry_class = scrapy.Field()

    spider_name = scrapy.Field()
    list_url = scrapy.Field()
    detail_url = scrapy.Field()
    status = scrapy.Field()
    error = scrapy.Field()






