import scrapy
from scrapy.http import HtmlResponse
from Data_collecting_hw.bookparser.items import BookparserItem

class Book24Spider(scrapy.Spider):
    name = 'book24'
    allowed_domains = ['book24.ru']
    start_urls = ['https://book24.ru/catalog/fantastika-1649/']

    def parse(self, response:HtmlResponse):
        book_links = response.xpath("//a[@class='product-card__name smartLink']/@href").extract()
        next_page = response.xpath("//link[@rel='next']/@href").extract_first()

        if next_page:
            yield response.follow(next_page, callback=self.parse)
        for link in book_links:
            yield response.follow(link, callback=self.book_parse)

    def book_parse(self, response: HtmlResponse):
        link = response.url
        name = response.css("h1::text").extract_first()
        authors = response.xpath("//a[@itemprop='author']/text()").extract_first()
        name_eng = None
        old_price = None
        new_price = None
        rate = None

        new_price = response.xpath("//div[@class='item-actions__price']/b/text()").extract_first()
        old_price = response.xpath("//div[@class='item-actions__price-old']/text()").extract_first()
        rate = response.xpath("//span[@class='rating__rate-value']/text()").extract_first()

        yield BookparserItem(link=link, name=name, name_eng=name_eng, authors=authors,
                           old_price=old_price, new_price=new_price, rate=rate)
