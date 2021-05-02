"""
1) Создать двух пауков по сбору данных о книгах с сайтов labirint.ru и book24.ru
2) Каждый паук должен собирать:
* Ссылку на книгу
* Наименование книги
* Автор(ы)
* Основную цену
* Цену со скидкой
* Рейтинг книги
3) Собранная информация дожна складываться в базу данных
"""
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from bookparser import settings
from Data_collecting_hw.bookparser.spiders.labirint import LabirintSpider
from Data_collecting_hw.bookparser.spiders.book24 import Book24Spider

if __name__ == "__main__":

    crawler_settings = Settings()
    crawler_settings.setmodule(settings)

    process = CrawlerProcess(settings=crawler_settings)
    process.crawl(LabirintSpider)
    process.crawl(Book24Spider)

    process.start()
