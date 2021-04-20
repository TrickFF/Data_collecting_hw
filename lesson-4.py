"""
Задание 1
Написать приложение, которое собирает основные новости с сайтов news.mail.ru,
lenta.ru, yandex-новости. Для парсинга использовать XPath.
Структура данных должна содержать:
название источника;
наименование новости;
ссылку на новость;
дата публикации.

Задание 2
Сложить собранные данные в БД

"""

from lxml import html
import requests
from pymongo import MongoClient
import datetime
from pprint import pprint

client = MongoClient('127.0.0.1', 27017)
db = client['news_scrapping']
news_db = db.news

header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                        ' Chrome/89.0.4389.86 YaBrowser/21.3.1.185 Yowser/2.5 Safari/537.36'}
response_lt = requests.get('https://lenta.ru/')
response_ya = requests.get('https://yandex.ru/news/')
response_mr = requests.get('https://news.mail.ru/')

news_data = []

dom = html.fromstring(response_lt.text)
items = dom.xpath("//section[@class='row b-top7-for-main js-top-seven']/div[@class='span4']/div[@class='item']")

# Собираем информацию по новостям с lenta.ru
for item in items:
    news = {}
    source = 'https://lenta.ru'
    name = item.xpath("./a/text()")[0]

    # иногда в блоке новостей проскакивают новости со сторонних источников
    # если ошибка, то искать тут
    link = source + item.xpath("./a[contains(@href, '/news/2')]/@href")[0] if\
        item.xpath("./a[contains(@href, '/news/2')]/@href") else\
        item.xpath("./a[contains(@class, 'b-link-external')]/@href")[0]

    # Приводим дату/время новостей к единому формату в секундах
    time = item.xpath("./a/time/@datetime")[0]
    time_str  = time.replace(' января ', '-01-').replace(' февраля ', '-02-').replace(' марта ', '-03-')\
        .replace(' апреля ', '-04-').replace(' мая ', '-05-').replace(' июня ', '-06-')\
        .replace(' июля ', '-07-').replace(' августа ', '-08-').replace(' сентября ', '-09-')\
        .replace(' октября ', '-10-').replace(' ноября ', '-11-').replace(' декабряя ', '-12-').split(sep=', ')
    time_str[1] = time_str[1].split(sep='-')
    time_str[1] = str(time_str[1][2] + '-' + time_str[1][1] + '-' + time_str[1][0])
    time_str = (datetime.datetime.strptime(str(time_str[1] + time_str[0]),
                                                                     "%Y-%m-%d %H:%M")).timestamp()

    name_str = name.replace('\xa0', ' ')

    news['source'] = source
    news['name'] = name_str
    news['link'] = link
    news['time'] = time_str

    news_data.append(news)

dom = html.fromstring(response_ya.text)
items = dom.xpath("//div[@class='mg-grid__row mg-grid__row_gap_8 news-top-flexible-stories news-app__top']/div/article")

# Собираем информацию по новостям с yandex.ru/news
for item in items:
    news = {}
    source_name = item.xpath(".//a/@aria-label")[0] if item.xpath(".//a/@aria-label")[0] else ''
    source = source_name.replace('Источник: ', '')
    link = item.xpath(".//div/a/@href")[0]
    name_str = str(item.xpath(".//a/h2/text()")[0]).replace('\xa0', ' ')

    # Приводим дату/время новостей к единому формату в секундах
    time = str(datetime.datetime.now().date()) + " " +\
           str(item.xpath(".//span[@class='mg-card-source__time']/text()")[0]).replace('вчера в ', '')

    time_str = (datetime.datetime.strptime(time, "%Y-%m-%d %H:%M")).timestamp()

    news['source'] = source
    news['name'] = name_str
    news['link'] = link
    news['time'] = time_str

    news_data.append(news)

dom = html.fromstring(response_mr.text)
items = dom.xpath(".//div/ul[@class='list list_type_square list_half js-module']/li")

# Функция сбора информации со страницы новости news.mail.ru
def page_scarp(link):
    response_mr_page = requests.get(link)
    dom = html.fromstring(response_mr_page.text)
    elements = dom.xpath(".//div[contains(@class, 'js-article')]")
    for el in elements:
        name = str(el.xpath(".//h1/text()")[0])
        source = el.xpath(".//span[@class='link__text']/text()")[0] if\
            el.xpath(".//span[@class='link__text']/text()")[0] else ''

        # Приводим дату/время новостей к единому формату в секундах
        time = el.xpath(".//span[contains(@datetime, ':')]/@datetime")[0] if\
            el.xpath(".//span[contains(@datetime, ':')]/@datetime")[0] else ''
        time_str = (datetime.datetime.strptime(time.split(sep='+')[0].replace('T', ' '),
                                                                         "%Y-%m-%d %H:%M:%S")).timestamp()

        return name, source, time_str

# Собираем информацию по новостям с news.mail.ru
for item in items:
    news = {}
    link = item.xpath(".//a/@href")[0]
    page_scarp(link)

    news['source'] = page_scarp(link)[1]
    news['name'] = page_scarp(link)[0]
    news['link'] = link
    news['time'] = page_scarp(link)[2]
    news_data.append(news)


# Очистка всей коллекции
news_db.delete_many({})


# Переменная хранит количество новостей до импорта
count_1 = db.news.estimated_document_count()


# Импорт/обнвление данных по новостям в базе
if news_data:
    for nst in news_data:
        news_db.update_one({'link': nst['link']}, {'$set': {'link': nst['link'], 'name': nst['name'],
                                                            'source': nst['source'], 'time': nst['time']}}, upsert=True)


# Вывод последних 10 новостей из базы
for el in news_db.find({}, limit=10).sort('time', -1):
    print(f'\nНовость : {el["name"]}')
    print(f'Ссылка  : {el["link"]}')
    print(f'Источник: {el["source"]}')
    print(f'Дата    : {datetime.datetime.fromtimestamp(el["time"]).strftime("%Y-%m-%d %H:%M:%S")}')


print(f'\nНовостей в базе до импорта данных: {count_1}')
print(f'Новостей в базе после импорта: {db.news.estimated_document_count()}')
print(f'Добавлено {db.news.estimated_document_count() - count_1} новостей')

"""
Результат:

Новость : МИД заявил об имуществе Чехии после идеи отнять землю посольства в Праге
Ссылка  : https://yandex.ru/news/story/MID_zayavil_ob_imushhestve_CHekhii_posle_idei_otnyat_zemlyu_posolstva_vPrage--2ed4ce6d3a6a2277ede146a3ec90a53c?lang=ru&rubric=index&fan=1&stid=t74gzHxVFuOTiWVuCzS4&t=1618867703&tt=true&persistent_id=140566478
Источник: РБК
Дата    : 2021-04-20 23:46:04

Новость : Бабиш отказался считать взрыв в Врбетице нападением России на Чехию
Ссылка  : https://yandex.ru/news/story/Babish_otkazalsya_schitat_vzryv_vVrbetice_napadeniem_Rossii_naCHekhiyu--53f842dca7508dadd015a7cd06146171?lang=ru&rubric=index&fan=1&stid=TGCC8uoiU_JC-nkDEt9-&t=1618867703&tt=true&persistent_id=140556955
Источник: РБК
Дата    : 2021-04-20 23:37:04

Новость : Младенец оказался под завалами после взрыва жилого дома в Нижегородской области
Ссылка  : https://lenta.ru/news/2021/04/19/vzryv/
Источник: https://lenta.ru
Дата    : 2021-04-20 00:35:04

Новость : День в истории: 20 апреля
Ссылка  : https://news.mail.ru/society/46002206/
Источник: Новости Mail.ru
Дата    : 2021-04-20 00:30:47

Новость : ВОЗ назвала сроки взятия коронавируса под контроль
Ссылка  : https://lenta.ru/news/2021/04/20/control/
Источник: https://lenta.ru
Дата    : 2021-04-20 00:24:04

Новость : Боровой назвал подталкивавших Ельцина к войне в Чечне людей
Ссылка  : https://lenta.ru/news/2021/04/20/push/
Источник: https://lenta.ru
Дата    : 2021-04-20 00:21:04

Новость : Вице-премьер Борисов предупредил о риске катастрофы на МКС
Ссылка  : https://yandex.ru/news/story/Vice-premer_Borisov_predupredil_oriske_katastrofy_naMKS--7e3460c996f624503e501f2a40a475e1?lang=ru&rubric=index&fan=1&stid=EAA1iVMQUWc1NtNSsy6S&t=1618867703&tt=true&persistent_id=140560464
Источник: Известия
Дата    : 2021-04-20 00:20:04

Новость : Олимпийский чемпион предложил норвежцу мыло и веревку после критики формы России
Ссылка  : https://lenta.ru/news/2021/04/20/vasiliev/
Источник: https://lenta.ru
Дата    : 2021-04-20 00:13:04

Новость : Диетолог описала безопасную для здоровья порцию шашлыка
Ссылка  : https://lenta.ru/news/2021/04/20/shashlyk/
Источник: https://lenta.ru
Дата    : 2021-04-20 00:10:04

Новость : Смартфон Samsung взорвался в рюкзаке владельца
Ссылка  : https://lenta.ru/news/2021/04/20/samsungfail/
Источник: https://lenta.ru
Дата    : 2021-04-20 00:10:04

Новостей в базе до импорта данных: 22
Новостей в базе после импорта: 28
Добавлено 6 новостей

"""
