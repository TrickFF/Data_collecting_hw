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
    time_str = (datetime.datetime.now() - datetime.datetime.strptime(str(time_str[1] + time_str[0]),
                                                                     "%Y-%m-%d %H:%M")).total_seconds()

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
    name = str(item.xpath(".//div/div/text()")[0])
    name_str = name.replace('\xa0', ' ')

    # Приводим дату/время новостей к единому формату в секундах
    time = str(datetime.datetime.now().date()) + " " + str(item.xpath(".//span[@class='mg-card-source__time']/text()")[0])
    time_str = (datetime.datetime.now() - datetime.datetime.strptime(time, "%Y-%m-%d %H:%M")).total_seconds()

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
        time_str = (datetime.datetime.now() - datetime.datetime.strptime(time.split(sep='+')[0].replace('T', ' ')[:-3],
                                                                         "%Y-%m-%d %H:%M")).total_seconds()

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
# ews_db.delete_many({})

# Переменная хранит количество новостей до импорта
count_1 = db.news.estimated_document_count()

# Импорт/обнвление данных по новостям в базе
if news_data:
    for nst in news_data:
        news_db.update_one({'link': nst['link']}, {'$set': {'link': nst['link'], 'name': nst['name'],
                                                            'source': nst['source'], 'time': nst['time']}}, upsert=True)

# Вывод последних 10 новостей из базы
for el in news_db.find({}, limit=10).sort('time', 1):
    print(f'\nНовость : {el["name"]}')
    print(f'Ссылка  : {el["link"]}')
    print(f'Источник: {el["source"]}')
    now_time = (datetime.datetime.now()).timestamp()
    print(f'Дата:   {datetime.datetime.fromtimestamp(now_time - el["time"]).strftime("%Y-%m-%d %H:%M:%S")}')


print(f'\nНовостей в базе до импорта данных: {count_1}')
print(f'Новостей в базе после импорта: {db.news.estimated_document_count()}')
print(f'Добавлено {db.news.estimated_document_count() - count_1} новостей')

"""
Результат:

Новость : Раскрыт лучший план действий при потере путевки в Турцию
Ссылка  : https://lenta.ru/news/2021/04/19/luchshiy/
Источник: https://lenta.ru
Дата:   2021-04-19 20:53:04

Новость : Премьер-министр Чехии Андрей Бабиш отказался считать взрывы на складе боеприпасов во Врбетице актом государственного терроризма.
Ссылка  : https://yandex.ru/news/story/Premer_CHekhii_otkazalsya_schitat_vzryvy_vo_Vrbetice_terrorizmom--a3a7ecabd83fc1923a7ae25b33071075?lang=ru&rubric=index&fan=1&stid=0c5irYvW-nkD5QJI0Dj9&t=1618854903&tt=true&persistent_id=140556955
Источник: Lenta.ru
Дата:   2021-04-19 20:52:04

Новость : 12 ведущих клубов Англии, Испании и Италии объявили о создании Суперлиги В ночь на понедельник в европейском футболе произошло важнейшее событие, которое может иметь глобальные последствия для всего мирового спорта.
Ссылка  : https://yandex.ru/sport/story/12_vedushhikh_klubov_Anglii_Ispanii_i_Italii_obyavili_osozdanii_Superligi--670249e9bbb1b4f9a3078a5cd348840c?lang=ru&rubric=index&fan=1&stid=AQsZy6aoH0kziwdTov00&t=1618854781&tt=true&persistent_id=140462953&utm_source=yxnews&utm_medium=desktop
Источник: Коммерсантъ
Дата:   2021-04-19 20:50:54

Новость : Власти Праги потребовали от России вернуть часть городского парка Стромовка, которую занимает сейчас российское посольство в столице Чехии, заявил староста района «Прага-7» Ян Чижински в Twitter.
Ссылка  : https://yandex.ru/news/story/Vlasti_Pragi_potrebovali_otposolstva_Rossii_vernut_chast_parka_Stromovka--6dbfd85c6c78c24f882921e7fcddec08?lang=ru&rubric=index&fan=1&stid=gTgFckOeRs5CCzS4O2O1&t=1618853895&tt=true&persistent_id=140539116
Источник: Ведомости
Дата:   2021-04-19 20:50:47

Новость : Участки российского посольства в Чехии были выделены СССР в начале 70-х годов на основании действующих советско-чехословацких соглашений.
Ссылка  : https://yandex.ru/news/story/MID_RF_otreagiroval_natrebovanie_CHekhii_vernut_chast_parka_Stromovka--39a3053e31e27389d898e8572c5cccd2?lang=ru&rubric=index&fan=1&stid=ZnuVCzS4Rs5CS1wSO2O1&t=1618854337&tt=true&persistent_id=140539116
Источник: Известия
Дата:   2021-04-19 20:50:36

Новость : В Москве задержали развращавшего детей в социальных сетях россиянина
Ссылка  : https://lenta.ru/news/2021/04/19/zaderzhali/
Источник: https://lenta.ru
Дата:   2021-04-19 20:50:04

Новость : Фракция президентской партии "Слуга народа" в Верховной раде потребовала расторжения дипломатических отношений с Россией.
Ссылка  : https://yandex.ru/news/story/Frakciya_Zelenskogo_vRade_potrebovala_rastorzheniya_dipotnoshenij_sRossiej--215a3f71cf71cfe89184c075a6eb0738?lang=ru&rubric=index&fan=1&stid=KWZ0WHG1W3nWMh_OloMm&t=1618854903&tt=true&persistent_id=140557207
Источник: ТАСС
Дата:   2021-04-19 20:50:04

Новость : Федеральная антимонопольная служба (ФАС) России возбудила дело в отношении Google, так как принадлежащий ему Youtube, по мнению ведомства, злоупотребляет своим доминирующим положением на рынке.
Ссылка  : https://yandex.ru/news/story/FAS_vozbudila_delo_votnoshenii_Google_iz-zadejstvij_Youtube--f653ba34ed067cc5afbe770b58175dda?lang=ru&rubric=index&fan=1&stid=OmEorDzd_jlCENjhmkei&t=1618853895&tt=true&persistent_id=140550813
Источник: Ведомости
Дата:   2021-04-19 20:49:47

Новость : Власти Праги потребовали от России вернуть часть городского парка Стромовка, которую занимает сейчас российское посольство в столице Чехии, заявил староста района «Прага-7» Ян Чижински в Twitter.
Ссылка  : https://yandex.ru/news/story/Vlasti_Pragi_potrebovali_otposolstva_Rossii_vernut_chast_parka_Stromovka--6dbfd85c6c78c24f882921e7fcddec08?lang=ru&rubric=index&fan=1&stid=ckOeRs5CCzS4S1wSO2O1&t=1618854116&tt=true&persistent_id=140539116
Источник: Ведомости
Дата:   2021-04-19 20:49:31

Новость : Премьер-министр Чехии Андрей Бабиш отказался считать взрывы на складе боеприпасов во Врбетице актом государственного терроризма.
Ссылка  : https://yandex.ru/news/story/Premer_CHekhii_otkazalsya_schitat_vzryvy_vo_Vrbetice_terrorizmom--a3a7ecabd83fc1923a7ae25b33071075?lang=ru&rubric=index&fan=1&stid=0c5i-nkDrYvW5QJI0Dj9&t=1618854559&tt=true&persistent_id=140556955
Источник: Lenta.ru
Дата:   2021-04-19 20:47:51

Новостей в базе до импорта данных: 46
Новостей в базе после импорта: 51
Добавлено 5 новостей

"""
