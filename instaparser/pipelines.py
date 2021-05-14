# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient


class InstaparserPipeline:
    def __init__(self):
        client = MongoClient('localhost', 27017)
        self.mongo_base = client.instagram

    def process_item(self, item, spider):
        collection = self.mongo_base[spider.name]
        # _id формируется конкатенацией id пользователя, которого скрапим, id пользователя который/которого фоловит
        # и признака follow_tag (0/1)
        item['_id'] = str(item['user_id'])+str(item['follow_id'])+str(item['follow_tag'])
        collection.update_one({'_id': item['_id']}, {'$set': {'user_id': item['user_id'], 'user_2': item['follow_id'],
                            'follow_tag': item['follow_tag'], 'user_2_name': item['follow_name'],
                            'user_2_full_name': item['follow_full_name'], 'user_2_avatar': item['follow_avatar']}}, upsert=True)


        return item
