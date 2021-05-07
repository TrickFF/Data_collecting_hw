import scrapy
from scrapy.http import HtmlResponse
from Data_collecting_hw.leroyparser.items import LeroyparserItem
from scrapy.loader import ItemLoader


class LeroySpider(scrapy.Spider):
    name = 'leroy'
    allowed_domains = ['leroymerlin.ru']
    start_urls = ['http://leroymerlin.ru/']

    def __init__(self, query):
        super(LeroySpider, self).__init__()
        self.start_urls = [f'https://leroymerlin.ru/search/?q={query}&family=kovry-201709&suggest=true']

    def parse(self, response:HtmlResponse):
        goods_links = response.xpath("//a[contains(@href, '/product/') and contains(@tabindex, '-1')]/@href").extract()
        next_page = response.xpath("//a[contains(@aria-label, 'Следующая страница:')]/@href").extract_first()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
        for link in goods_links:
            yield response.follow(link, callback=self.pasrse_goods)

    def pasrse_goods(self, response:HtmlResponse):
        loader = ItemLoader(item=LeroyparserItem(), response=response)
        loader.add_xpath('_id', "//span[@slot='article']/@content")
        loader.add_value('link', response.url)
        loader.add_xpath('name', "//h1/text()")
        loader.add_xpath('price', "//span[@slot='price']/text()")
        loader.add_xpath('prop_k', "//div/dt/text()") # наименование характеристик
        loader.add_xpath('prop_v', "//div/dd/text()") # значение характеристик
        loader.add_xpath('photos', "//uc-pdp-media-carousel/picture/source[contains(@media, '1024')]/@srcset")
        yield loader.load_item()
