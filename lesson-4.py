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

    # инггда в блоке новостей проскакивают новости со сторонних источников
    if item.xpath("./a[contains(@href, '/news/2')]/@href"):
        link = source + item.xpath("./a[contains(@href, '/news/2')]/@href")[0]
    else:
        link = item.xpath("./a[contains(@class, 'b-link-external')]/@href")[0]

    # Приводим дату/время новостей к единому формату
    time = item.xpath("./a/time/@datetime")[0]
    time_str  = time.replace(' января ', '-01-').replace(' февраля ', '-02-').replace(' марта ', '-03-')\
        .replace(' апреля ', '-04-').replace(' мая ', '-05-').replace(' июня ', '-06-')\
        .replace(' июля ', '-07-').replace(' августа ', '-08-').replace(' сентября ', '-09-')\
        .replace(' октября ', '-10-').replace(' ноября ', '-11-').replace(' декабряя ', '-12-').split(sep=', ')
    time_str[1] = time_str[1].split(sep='-')
    time_str[1] = str(time_str[1][2] + '-' + time_str[1][1] + '-' + time_str[1][0])
    time_str = str(time_str[1] + time_str[0])

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

    # Приводим дату/время новостей к единому формату
    time = str(datetime.datetime.now().date())+ " " + str(item.xpath(".//span[@class='mg-card-source__time']/text()")[0])

    news['source'] = source
    news['name'] = name_str
    news['link'] = link
    news['time'] = time

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
        source = el.xpath(".//span[@class='link__text']/text()")[0] if el.xpath(".//span[@class='link__text']/text()")[0] else ''

        # Приводим дату/время новостей к единому формату
        time = el.xpath(".//span[contains(@datetime, ':')]/@datetime")[0] if el.xpath(".//span[contains(@datetime, ':')]/@datetime")[0] else ''
        time_str = time.split(sep='+')[0].replace('T', ' ')[:-3]
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
# news_db.delete_many({})

# Переменная хранит количество новостей до импорта
count_1 = db.news.estimated_document_count()

# Импорт/обнвление данных по новостям в базе
if news_data:
    for str in news_data:
        pprint(str)
        news_db.update_one({'link': str['link']}, {'$set': {'link': str['link'], 'name': str['name'],
                                                            'source': str['source'], 'time': str['time']}}, upsert=True)

# Вывод данных из базы
for el in news_db.find({}):
    pprint((el))

print(f'\nНовостей в базе до импорта данных: {count_1}')
print(f'Новостей в базе после импорта: {db.news.estimated_document_count()}')
print(f'Добавлено {db.news.estimated_document_count() - count_1} новостей')

"""
Результат:

{'link': 'https://lenta.ru/news/2021/04/19/protest/',
 'name': 'Песков предупредил о реакции полиции на несогласованные акции '
         'протеста',
 'source': 'https://lenta.ru',
 'time': '2021-04-19 14:25'}
{'link': 'https://lenta.ru/news/2021/04/19/ps4/',
 'name': 'В России закончились PlayStation 4',
 'source': 'https://lenta.ru',
 'time': '2021-04-19 14:20'}
{'link': 'https://lenta.ru/news/2021/04/19/kremlbedn/',
 'name': 'Кремль оценил уровень бедности в России',
 'source': 'https://lenta.ru',
 'time': '2021-04-19 14:18'}
{'link': 'https://lenta.ru/news/2021/04/19/klimm/',
 'name': 'Россиянам пообещали климатические качели в мае',
 'source': 'https://lenta.ru',
 'time': '2021-04-19 14:16'}
{'link': 'https://lenta.ru/news/2021/04/19/cl_new/',
 'name': 'УЕФА утвердил проект обновленной Лиги чемпионов',
 'source': 'https://lenta.ru',
 'time': '2021-04-19 14:16'}
{'link': 'https://lenta.ru/news/2021/04/19/ukr_exp/',
 'name': 'Украина вышлет российского дипломата из Киева',
 'source': 'https://lenta.ru',
 'time': '2021-04-19 14:15'}
{'link': 'https://lenta.ru/news/2021/04/19/putin_poslanie/',
 'name': 'Кремль назвал участников послания Путина парламенту',
 'source': 'https://lenta.ru',
 'time': '2021-04-19 14:15'}
{'link': 'https://lenta.ru/news/2021/04/19/pozner/',
 'name': 'Познер перечислил преимущества российских женщин перед мужчинами',
 'source': 'https://lenta.ru',
 'time': '2021-04-19 14:13'}
{'link': 'https://lenta.ru/news/2021/04/19/ygroza/',
 'name': 'Кремль отреагировал на угрозы США о последствиях в случае смерти '
         'Навального',
 'source': 'https://lenta.ru',
 'time': '2021-04-19 14:02'}
{'link': 'https://yandex.ru/news/story/Glava_MID_CHekhii_schel_silnym_otvet_Rossii_navysylku_diplomatov--86eff76663f7ee05909f1fd8c9a022b5?lang=ru&rubric=index&fan=1&stid=ue0FCuY7W96wGwv2GyzZ&t=1618831226&tt=true&persistent_id=140518203',
 'name': 'Реакция Москвы на высылку российских дипломатов из Чехии оказалась '
         'сильнее, чем того ожидали в Праге.',
 'source': 'РБК',
 'time': '2021-04-19 14:15'}
{'link': 'https://yandex.ru/news/story/VKremle_podtverdili_chto_Putin_i_Bajden_obsudili_popytku_perevorota_vBelorussii--01346b92b65ddde9b0cc9561852029a9?lang=ru&rubric=index&fan=1&stid=-2M-XUGmCeGGtrS13Qfy&t=1618831226&tt=true&persistent_id=140456831',
 'name': 'Представитель Кремля Дмитрий Песков заявил, что президенты России и '
         'США Владимир Путин и Джо Байден во время разговора по телефону '
         'затронули попытку госпереворота на территории Белоруссии.',
 'source': 'Газета.Ru',
 'time': '2021-04-19 14:17'}
{'link': 'https://yandex.ru/news/story/MVD_Rossii_prizvalo_grazhdan_ne_uchastvovat_vnesoglasovannykh_akciyakh--4110e90148756441a0714dbba011b523?lang=ru&rubric=index&fan=1&stid=GzeWkcL0uWERzqmONkPL&t=1618831226&tt=true&persistent_id=140523375',
 'name': 'МВД призывает россиян воздержаться от участия в несогласованных '
         'акциях, сообщается на сайте ведомства.',
 'source': 'RT на русском',
 'time': '2021-04-19 14:16'}
{'link': 'https://yandex.ru/news/story/Navalnogo_perevodyat_izkolonii_vstacionar_bolnicy_dlyaosuzhdennykh--be7f23b513a615271b41112e68f764d4?lang=ru&rubric=index&fan=1&stid=PFFkvYtFnaSPJU5GVcay&t=1618831226&tt=true&persistent_id=140518498',
 'name': '«Комиссией врачей ФКУЗ МСЧ-33 ФСИН России было принято решение о '
         'переводе А. Навального в стационар областной больницы для '
         'осужденных, располагающейся на территории ИК-3 УФСИН России по '
         'Владимирской области, которая, в том числе, специализируется на '
         'динамическом наблюдении за подобными пациентами»,— отмечается в '
         'сообщении ФСИН.',
 'source': 'Коммерсантъ',
 'time': '2021-04-19 14:09'}
{'link': 'https://yandex.ru/news/story/Deripaska_zayavil_o80_mln_rossiyan_sdokhodami_nizhe_prozhitochnogo_minimuma--45fb5b6834918bafb239942e9ffdf401?lang=ru&rubric=index&fan=1&stid=XnVQ-n_2wei7oWXNCuN1&t=1618831226&tt=true&persistent_id=140508541',
 'name': 'Служба статистики оценила число россиян, чьи доходы находятся ниже '
         'прожиточного минимума, в 17,8 млн человек.',
 'source': 'Коммерсантъ',
 'time': '2021-04-19 14:15'}
{'link': 'https://sportmail.ru/news/football-rus-premier/46008941/',
 'name': '«Зенит» отказался от участия в Суперлиге Европы',
 'source': 'Lenta.Ru',
 'time': '2021-04-19 13:50'}
{'link': 'https://news.mail.ru/society/46009058/',
 'name': 'Вертолет на Марсе: аппарат NASA «Индженьюити» попытался совершить '
         'первый полет',
 'source': 'BBC News Русская служба',
 'time': '2021-04-19 13:52'}
{'link': 'https://news.mail.ru/society/46002478/',
 'name': 'В Гидрометцентре рассказали, каким будет лето в 2021 году',
 'source': 'ТАСС',
 'time': '2021-04-19 02:03'}
{'link': 'https://news.mail.ru/society/46010267/',
 'name': 'Окрестности Кейптауна охватил крупный пожар (видео)',
 'source': 'Новости Mail.ru',
 'time': '2021-04-19 14:06'}
{'link': 'https://news.mail.ru/economics/46006911/',
 'name': 'Богатейший депутат отчитался о доходе в 6,3 млрд рублей',
 'source': 'Коммерсантъ',
 'time': '2021-04-19 11:21'}
{'link': 'https://news.mail.ru/society/46009787/',
 'name': 'В Панаме «обезвредили» кота-наркокурьера',
 'source': 'Новости Mail.ru',
 'time': '2021-04-19 13:37'}
{'link': 'https://news.mail.ru/politics/46006563/',
 'name': 'ЕС призвал Россию отвести войска от границы с Украиной',
 'source': 'ТАСС',
 'time': '2021-04-19 11:05'}
{'link': 'https://news.mail.ru/society/46005112/',
 'name': 'Турецкий ученый опроверг одобрение производства «Спутника V» в '
         'стране',
 'source': 'РБК',
 'time': '2021-04-19 09:31'}
{'_id': ObjectId('607d684508fb8b87d4c11a4d'),
 'link': 'https://lenta.ru/news/2021/04/19/ps4/',
 'name': 'В России закончились PlayStation 4',
 'source': 'https://lenta.ru',
 'time': '2021-04-19 14:20'}
{'_id': ObjectId('607d684508fb8b87d4c11a4f'),
 'link': 'https://lenta.ru/news/2021/04/19/kremlbedn/',
 'name': 'Кремль оценил уровень бедности в России',
 'source': 'https://lenta.ru',
 'time': '2021-04-19 14:18'}
{'_id': ObjectId('607d684508fb8b87d4c11a51'),
 'link': 'https://lenta.ru/news/2021/04/19/klimm/',
 'name': 'Россиянам пообещали климатические качели в мае',
 'source': 'https://lenta.ru',
 'time': '2021-04-19 14:16'}
{'_id': ObjectId('607d684508fb8b87d4c11a53'),
 'link': 'https://lenta.ru/news/2021/04/19/cl_new/',
 'name': 'УЕФА утвердил проект обновленной Лиги чемпионов',
 'source': 'https://lenta.ru',
 'time': '2021-04-19 14:16'}
{'_id': ObjectId('607d684508fb8b87d4c11a55'),
 'link': 'https://lenta.ru/news/2021/04/19/ukr_exp/',
 'name': 'Украина вышлет российского дипломата из Киева',
 'source': 'https://lenta.ru',
 'time': '2021-04-19 14:15'}
{'_id': ObjectId('607d684508fb8b87d4c11a57'),
 'link': 'https://lenta.ru/news/2021/04/19/putin_poslanie/',
 'name': 'Кремль назвал участников послания Путина парламенту',
 'source': 'https://lenta.ru',
 'time': '2021-04-19 14:15'}
{'_id': ObjectId('607d684508fb8b87d4c11a59'),
 'link': 'https://lenta.ru/news/2021/04/19/pozner/',
 'name': 'Познер перечислил преимущества российских женщин перед мужчинами',
 'source': 'https://lenta.ru',
 'time': '2021-04-19 14:13'}
{'_id': ObjectId('607d684508fb8b87d4c11a5b'),
 'link': 'https://lenta.ru/news/2021/04/19/ygroza/',
 'name': 'Кремль отреагировал на угрозы США о последствиях в случае смерти '
         'Навального',
 'source': 'https://lenta.ru',
 'time': '2021-04-19 14:02'}
{'_id': ObjectId('607d684508fb8b87d4c11a5d'),
 'link': 'https://lenta.ru/news/2021/04/19/peskov/',
 'name': 'Песков прокомментировал сообщения о «критическом» состоянии '
         'Навального',
 'source': 'https://lenta.ru',
 'time': '2021-04-19 13:35'}
{'_id': ObjectId('607d684508fb8b87d4c11a5f'),
 'link': 'https://yandex.ru/news/story/Evrokomissiya_vyrazila_solidarnost_spoziciej_CHekhii_povysylke_rossijskikh_diplomatov--d2989c3d9be8d674161b90697932f091?lang=ru&rubric=index&fan=1&stid=_64KMzUEPkGpYWfXtRAg&t=1618830684&tt=true&persistent_id=140527483',
 'name': '"Глава Еврокомиссии Урсула фон дер Ляйен полностью солидарна с '
         'позицией Чехии", - заявил он в ответ на просьбу журналистов '
         'прокомментировать высылку российских дипломатов и объявление Прагой '
         'в розыск Александра Петрова и Руслана Боширова, якобы причастных ко '
         'взрыву склада боеприпасов в деревне Врбетице 16 октября 2014 года.',
 'source': 'ТАСС',
 'time': '2021-04-19 14:08'}
{'_id': ObjectId('607d684508fb8b87d4c11a61'),
 'link': 'https://yandex.ru/news/story/Peskov_Kreml_nikak_ne_vosprinyal_ugrozy_SSHA_oposledstviyakh_vsluchae_smerti_Navalnogo--302ee6eb3df6ad61cb6890f2a2bd760a?lang=ru&rubric=index&fan=1&stid=5_SA9lBqPu6yhwuyj2R1&t=1618830684&tt=true&persistent_id=140527289',
 'name': 'В Кремле "никак не восприняли" угрозы официальных лиц США о том, что '
         'Россия может столкнуться с последствиями в случае смерти Алексея '
         'Навального.',
 'source': 'ТАСС',
 'time': '2021-04-19 14:07'}
{'_id': ObjectId('607d684508fb8b87d4c11a63'),
 'link': 'https://yandex.ru/news/story/Peskov_zayavil_chto_tochechnye_mery_podderzhki_pomogli_sderzhat_rost_urovnya_bednosti--74f24ba734f8de3165e7f2dc8587e1e9?lang=ru&rubric=index&fan=1&stid=1PGnXnVQoWXNoxGD-n_2&t=1618830684&tt=true&persistent_id=140527381',
 'name': 'Уровень бедности населения вырос на фоне пандемии, но в России его '
         'удалось сдержать благодаря точечным мерам поддержки граждан.',
 'source': 'ТАСС',
 'time': '2021-04-19 14:09'}
{'_id': ObjectId('607d684508fb8b87d4c11a65'),
 'link': 'https://yandex.ru/news/story/MVD_Rossii_prizvalo_grazhdan_ne_uchastvovat_vnesoglasovannykh_akciyakh--4110e90148756441a0714dbba011b523?lang=ru&rubric=index&fan=1&stid=GzeWzqmONkPLuWERkcL0&t=1618830684&tt=true&persistent_id=140523375',
 'name': 'МВД призывает россиян воздержаться от участия в несогласованных '
         'акциях, сообщается на сайте ведомства.',
 'source': 'RT на русском',
 'time': '2021-04-19 14:07'}
{'_id': ObjectId('607d684508fb8b87d4c11a67'),
 'link': 'https://yandex.ru/news/story/VRossii_vyyavili_192_sluchaya_britanskogo_shtamma_koronavirusa--1f7be479c063c79e09da93c7931d6443?lang=ru&rubric=index&fan=1&stid=1KgoBJ4GIu72FmkY3yjl&t=1618830684&tt=true&persistent_id=140483218',
 'name': 'Более 190 случаев заболевания британским штаммом и свыше 20 — '
         'южноафриканским вариантом коронавируса выявлено в России по '
         'состоянию на 16 апреля.',
 'source': 'RT на русском',
 'time': '2021-04-19 14:08'}
{'_id': ObjectId('607d684508fb8b87d4c11a69'),
 'link': 'https://news.mail.ru/society/46002447/',
 'name': 'С 1 мая изменится размер и график получения пенсий: кого ждут '
         'доплаты, а кому перечислят деньги досрочно',
 'source': 'Life.ru',
 'time': '2021-04-19 12:10'}
{'_id': ObjectId('607d684508fb8b87d4c11a6b'),
 'link': 'https://news.mail.ru/society/46010267/',
 'name': 'Окрестности Кейптауна охватил крупный пожар (видео)',
 'source': 'Новости Mail.ru',
 'time': '2021-04-19 14:06'}
{'_id': ObjectId('607d684508fb8b87d4c11a6d'),
 'link': 'https://news.mail.ru/society/46009058/',
 'name': 'Вертолет на Марсе: аппарат NASA «Индженьюити» попытался совершить '
         'первый полет',
 'source': 'BBC News Русская служба',
 'time': '2021-04-19 13:52'}
{'_id': ObjectId('607d684508fb8b87d4c11a6f'),
 'link': 'https://news.mail.ru/society/46002478/',
 'name': 'В Гидрометцентре рассказали, каким будет лето в 2021 году',
 'source': 'ТАСС',
 'time': '2021-04-19 02:03'}
{'_id': ObjectId('607d684508fb8b87d4c11a71'),
 'link': 'https://news.mail.ru/society/46009787/',
 'name': 'В Панаме «обезвредили» кота-наркокурьера',
 'source': 'Новости Mail.ru',
 'time': '2021-04-19 13:37'}
{'_id': ObjectId('607d684508fb8b87d4c11a73'),
 'link': 'https://news.mail.ru/economics/46006911/',
 'name': 'Богатейший депутат отчитался о доходе в 6,3 млрд рублей',
 'source': 'Коммерсантъ',
 'time': '2021-04-19 11:21'}
{'_id': ObjectId('607d684508fb8b87d4c11a75'),
 'link': 'https://sportmail.ru/news/football-foreign/46009230/',
 'name': '«Тоттенхэм» объявил об уходе Жозе Моуринью',
 'source': 'Чемпионат.com',
 'time': '2021-04-19 13:20'}
{'_id': ObjectId('607d684508fb8b87d4c11a77'),
 'link': 'https://news.mail.ru/politics/46006563/',
 'name': 'ЕС призвал Россию отвести войска от границы с Украиной',
 'source': 'ТАСС',
 'time': '2021-04-19 11:05'}
{'_id': ObjectId('607d68ec08fb8b87d4c11a8b'),
 'link': 'https://yandex.ru/news/story/Glava_MID_CHekhii_schel_silnym_otvet_Rossii_navysylku_diplomatov--86eff76663f7ee05909f1fd8c9a022b5?lang=ru&rubric=index&fan=1&stid=ue0FCuY7W96wGwv2GyzZ&t=1618831003&tt=true&persistent_id=140518203',
 'name': 'Реакция Москвы на высылку российских дипломатов из Чехии оказалась '
         'сильнее, чем того ожидали в Праге.',
 'source': 'РБК',
 'time': '2021-04-19 14:15'}
{'_id': ObjectId('607d68ec08fb8b87d4c11a8d'),
 'link': 'https://yandex.ru/news/story/Peskov_zayavil_chto_tochechnye_mery_podderzhki_pomogli_sderzhat_rost_urovnya_bednosti--74f24ba734f8de3165e7f2dc8587e1e9?lang=ru&rubric=index&fan=1&stid=XnVQwei71PGnoWXNoxGD&t=1618831003&tt=true&persistent_id=140527381',
 'name': 'Уровень бедности населения вырос на фоне пандемии, но в России его '
         'удалось сдержать благодаря точечным мерам поддержки граждан.',
 'source': 'ТАСС',
 'time': '2021-04-19 14:14'}
{'_id': ObjectId('607d68ec08fb8b87d4c11a8f'),
 'link': 'https://yandex.ru/news/story/Navalnogo_perevodyat_izkolonii_vstacionar_bolnicy_dlyaosuzhdennykh--be7f23b513a615271b41112e68f764d4?lang=ru&rubric=index&fan=1&stid=PFFkvYtFnaSPVcayJU5G&t=1618831003&tt=true&persistent_id=140518498',
 'name': '«Комиссией врачей ФКУЗ МСЧ-33 ФСИН России было принято решение о '
         'переводе А. Навального в стационар областной больницы для '
         'осужденных, располагающейся на территории ИК-3 УФСИН России по '
         'Владимирской области, которая, в том числе, специализируется на '
         'динамическом наблюдении за подобными пациентами»,— отмечается в '
         'сообщении ФСИН.',
 'source': 'Коммерсантъ',
 'time': '2021-04-19 14:09'}
{'_id': ObjectId('607d68ec08fb8b87d4c11a91'),
 'link': 'https://yandex.ru/news/story/VKremle_podtverdili_chto_Putin_i_Bajden_obsudili_popytku_perevorota_vBelorussii--01346b92b65ddde9b0cc9561852029a9?lang=ru&rubric=index&fan=1&stid=XUGmCeGGtrS1q6WOJlf4&t=1618831003&tt=true&persistent_id=140456831',
 'name': 'Представитель Кремля Дмитрий Песков заявил, что президенты России и '
         'США Владимир Путин и Джо Байден во время разговора по телефону '
         'затронули попытку госпереворота на территории Белоруссии.',
 'source': 'Газета.Ru',
 'time': '2021-04-19 14:13'}
{'_id': ObjectId('607d68ec08fb8b87d4c11a93'),
 'link': 'https://yandex.ru/news/story/MVD_Rossii_prizvalo_grazhdan_ne_uchastvovat_vnesoglasovannykh_akciyakh--4110e90148756441a0714dbba011b523?lang=ru&rubric=index&fan=1&stid=GzeWzqmONkPLuWERkcL0&t=1618831003&tt=true&persistent_id=140523375',
 'name': 'МВД призывает россиян воздержаться от участия в несогласованных '
         'акциях, сообщается на сайте ведомства.',
 'source': 'RT на русском',
 'time': '2021-04-19 14:12'}
{'_id': ObjectId('607d68ec08fb8b87d4c11a95'),
 'link': 'https://sportmail.ru/news/football-rus-premier/46008941/',
 'name': '«Зенит» отказался от участия в Суперлиге Европы',
 'source': 'Lenta.Ru',
 'time': '2021-04-19 13:50'}
{'_id': ObjectId('607d68ec08fb8b87d4c11a9d'),
 'link': 'https://news.mail.ru/society/46005112/',
 'name': 'Турецкий ученый опроверг одобрение производства «Спутника V» в '
         'стране',
 'source': 'РБК',
 'time': '2021-04-19 09:31'}
{'_id': ObjectId('607d691a08fb8b87d4c11aa6'),
 'link': 'https://lenta.ru/news/2021/04/19/protest/',
 'name': 'Песков предупредил о реакции полиции на несогласованные акции '
         'протеста',
 'source': 'https://lenta.ru',
 'time': '2021-04-19 14:25'}
{'_id': ObjectId('607d694908fb8b87d4c11acc'),
 'link': 'https://yandex.ru/news/story/Glava_MID_CHekhii_schel_silnym_otvet_Rossii_navysylku_diplomatov--86eff76663f7ee05909f1fd8c9a022b5?lang=ru&rubric=index&fan=1&stid=ue0FCuY7W96wGwv2GyzZ&t=1618831226&tt=true&persistent_id=140518203',
 'name': 'Реакция Москвы на высылку российских дипломатов из Чехии оказалась '
         'сильнее, чем того ожидали в Праге.',
 'source': 'РБК',
 'time': '2021-04-19 14:15'}
{'_id': ObjectId('607d694908fb8b87d4c11ace'),
 'link': 'https://yandex.ru/news/story/VKremle_podtverdili_chto_Putin_i_Bajden_obsudili_popytku_perevorota_vBelorussii--01346b92b65ddde9b0cc9561852029a9?lang=ru&rubric=index&fan=1&stid=-2M-XUGmCeGGtrS13Qfy&t=1618831226&tt=true&persistent_id=140456831',
 'name': 'Представитель Кремля Дмитрий Песков заявил, что президенты России и '
         'США Владимир Путин и Джо Байден во время разговора по телефону '
         'затронули попытку госпереворота на территории Белоруссии.',
 'source': 'Газета.Ru',
 'time': '2021-04-19 14:17'}
{'_id': ObjectId('607d694908fb8b87d4c11ad0'),
 'link': 'https://yandex.ru/news/story/MVD_Rossii_prizvalo_grazhdan_ne_uchastvovat_vnesoglasovannykh_akciyakh--4110e90148756441a0714dbba011b523?lang=ru&rubric=index&fan=1&stid=GzeWkcL0uWERzqmONkPL&t=1618831226&tt=true&persistent_id=140523375',
 'name': 'МВД призывает россиян воздержаться от участия в несогласованных '
         'акциях, сообщается на сайте ведомства.',
 'source': 'RT на русском',
 'time': '2021-04-19 14:16'}
{'_id': ObjectId('607d694908fb8b87d4c11ad2'),
 'link': 'https://yandex.ru/news/story/Navalnogo_perevodyat_izkolonii_vstacionar_bolnicy_dlyaosuzhdennykh--be7f23b513a615271b41112e68f764d4?lang=ru&rubric=index&fan=1&stid=PFFkvYtFnaSPJU5GVcay&t=1618831226&tt=true&persistent_id=140518498',
 'name': '«Комиссией врачей ФКУЗ МСЧ-33 ФСИН России было принято решение о '
         'переводе А. Навального в стационар областной больницы для '
         'осужденных, располагающейся на территории ИК-3 УФСИН России по '
         'Владимирской области, которая, в том числе, специализируется на '
         'динамическом наблюдении за подобными пациентами»,— отмечается в '
         'сообщении ФСИН.',
 'source': 'Коммерсантъ',
 'time': '2021-04-19 14:09'}
{'_id': ObjectId('607d694908fb8b87d4c11ad4'),
 'link': 'https://yandex.ru/news/story/Deripaska_zayavil_o80_mln_rossiyan_sdokhodami_nizhe_prozhitochnogo_minimuma--45fb5b6834918bafb239942e9ffdf401?lang=ru&rubric=index&fan=1&stid=XnVQ-n_2wei7oWXNCuN1&t=1618831226&tt=true&persistent_id=140508541',
 'name': 'Служба статистики оценила число россиян, чьи доходы находятся ниже '
         'прожиточного минимума, в 17,8 млн человек.',
 'source': 'Коммерсантъ',
 'time': '2021-04-19 14:15'}
 
Новостей в базе до импорта данных: 30
Новостей в базе после импорта: 35
Добавлено 5 новостей
"""
