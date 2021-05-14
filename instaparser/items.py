# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class InstaparserItem(scrapy.Item):
    _id = scrapy.Field()
    user_id = scrapy.Field()
    follow_id = scrapy.Field()
    follow_tag = scrapy.Field()
    follow_name = scrapy.Field()
    follow_full_name = scrapy.Field()
    follow_avatar = scrapy.Field()
