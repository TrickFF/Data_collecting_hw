# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient


class BookparserPipeline:
    def __init__(self):
        client = MongoClient('127.0.0.1', 27017)
        self.db = client['books_scrapping']

    def process_item(self, item, spider):
        collection = self.db[spider.name]
        item = dict(item)
        if spider.name == 'book24':
            item['name'] = item['name'].rstrip()
            item['new_price'] = float(item['new_price'].replace(' ', ''))
            if item['old_price']:
                item['old_price'] = float(item['old_price'].replace(' р.', '').replace(' ', ''))
            if item['rate']:
                item['rate'] = float(item['rate'].replace(',', '.'))


        collection.update_one({'link': item['link']}, {'$set': {'link': item['link'], 'name': item['name'],
                                                                    'name_eng': item['name_eng'],
                                                                    'authors': item['authors'],
                                                                    'old_price': item['old_price'],
                                                                    'new_price': item['new_price'],
                                                                    'rate': item['rate']}}, upsert=True)
        return item
