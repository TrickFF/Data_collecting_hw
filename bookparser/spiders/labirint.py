import scrapy
from scrapy.http import HtmlResponse
from Data_collecting_hw.bookparser.items import BookparserItem

class LabirintSpider(scrapy.Spider):
    name = 'labirint'
    allowed_domains = ['labirint.ru']
    start_urls = ['https://www.labirint.ru/genres/2537/']


    def parse(self, response:HtmlResponse):
        book_links = response.xpath("//a[@class='product-title-link']/@href").extract()
        next_page = response.xpath("//a[@title='Следующая (Ctrl ->)']/@href").extract_first()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
        for link in book_links:
            yield response.follow(link, callback=self.book_parse)

    def book_parse(self, response:HtmlResponse):
        link = response.url
        name = response.css("h1::text").extract_first()
        name_eng = response.css("h2.h2_eng::text").extract_first()
        authors = response.xpath("//div[@class='authors']/a[@data-event-label='author']/text()").extract_first()
        if response.css("span.buying-price-val-number::text").extract_first():
            old_price = float(response.css("span.buying-price-val-number::text").extract_first())
            new_price = None
        else:
            old_price = float(response.css("span.buying-priceold-val-number::text").extract_first())
            new_price = float(response.css("span.buying-pricenew-val-number::text").extract_first())
        rate = float(response.xpath("//div[@id='rate']/text()").extract_first())
        yield BookparserItem(link=link, name=name, name_eng=name_eng, authors=authors,
                             old_price=old_price, new_price=new_price, rate=rate)
