"""
Задание 2
Написать программу, которая собирает «Новинки» с сайта техники mvideo и складывает данные в БД.
 Магазины можно выбрать свои. Главный критерий выбора: динамически загружаемые товары
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
from pprint import pprint
import json
from pymongo import MongoClient

client = MongoClient('127.0.0.1', 27017)
db = client['mvideo_scrapping']
goods_db = db.goods

options = Options()
options.add_argument('start-maximized')

binary_yandex_driver_file = 'yandexdriver.exe'

driver = webdriver.Chrome(binary_yandex_driver_file, options=options)
driver.get('https://www.mvideo.ru/')

section = driver.find_element_by_xpath("//div[contains(text(), 'Новинки')]")
actions = ActionChains(driver)
actions.move_to_element(section)
actions.perform()

goods = driver.find_elements_by_xpath("//ul[contains(@data-init-param, '\"title\":\"Новинки\"')]/li")
goods_count = len(goods)

while True:
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//ul[contains(@data-init-param, '\"title\":\"Новинки\"')]/../../a[@class='next-btn c-btn c-btn_scroll-horizontal c-btn_icon i-icon-fl-arrow-right']"))
    )
    button.click()
    sleep(2)
    goods = driver.find_elements_by_xpath("//ul[contains(@data-init-param, '\"title\":\"Новинки\"')]/li")
    goods_count_click = len(goods)

    if goods_count == goods_count_click:
        break
    goods_count = len(goods)

goods_data = []

for good in goods:
    info = good.find_element_by_class_name("sel-product-tile-title").get_attribute("data-product-info")
    info = json.loads(info)
    info['productPriceLocal'] = float(info['productPriceLocal'])
    info['link'] = 'https://www.mvideo.ru/products/' + info['productId']
    goods_data.append(info)

# Закрытие окна
driver.close()

# Очистка всей коллекции
# goods_db.delete_many({})

# Переменная хранит количество новостей до импорта
count_1 = db.goods.estimated_document_count()

# Импорт/обнвление данных по новостям в базе
if goods_data:
    for elem in goods_data:
        goods_db.update_one({'_id': elem['productId']}, {'$set': {'_id': elem['productId'], 'Location': elem['Location'], 'eventPosition': elem['eventPosition'],
                            'productCategoryId': elem['productCategoryId'], 'productCategoryName': elem['productCategoryName'],
                            'productGroupId': elem['productGroupId'], 'productName': elem['productName'],
                            'productPriceLocal': elem['productPriceLocal'], 'productVendorName': elem['productVendorName'], 'link': elem['link']}}, upsert=True)


# Вывод последних 10 товаров из базы
for el in goods_db.find({}, limit=10):
    print(f'ID товара          : {el["_id"]}\n'
          f'Наименование товара: {el["productName"]}\n'
          f'Стоимость товара   : {el["productPriceLocal"]}\n'
          f'Категория товара   : {el["productCategoryName"]}\n'
          f'ссылка на товар    : {el["link"]}\n')

print(f'\nТоваров в базе до импорта данных: {count_1}')
print(f'Товаров в базе после импорта: {db.goods.estimated_document_count()}')
print(f'Добавлено {db.goods.estimated_document_count() - count_1} товаров')
"""
Результат:

ID товара          : 10026051
Наименование товара: Электрический самокат Mizar Glock Pro (MIZ-MZGLOCKPRO)
Стоимость товара   : 38990.0
Категория товара   : Электросамокаты
ссылка на товар    : https://www.mvideo.ru/products/10026051

ID товара          : 30056205
Наименование товара: Смартфон Samsung Galaxy A52 128GB Awesome Violet (SM-A525F)
Стоимость товара   : 26990.0
Категория товара   : Смартфоны
ссылка на товар    : https://www.mvideo.ru/products/30056205

ID товара          : 30056199
Наименование товара: Смартфон Samsung Galaxy A72 128GB Awesome Blue (SM-A725F)
Стоимость товара   : 35990.0
Категория товара   : Смартфоны
ссылка на товар    : https://www.mvideo.ru/products/30056199

ID товара          : 30055841
Наименование товара: Смарт-браслет Honor Band 6 Sandstone Grey (ARG-B39)
Стоимость товара   : 3490.0
Категория товара   : Фитнес-браслеты
ссылка на товар    : https://www.mvideo.ru/products/30055841

ID товара          : 50149764
Наименование товара: Наушники True Wireless Huawei Freebuds 4i Carbon Black
Стоимость товара   : 7990.0
Категория товара   : Наушники
ссылка на товар    : https://www.mvideo.ru/products/50149764

ID товара          : 10026091
Наименование товара: Телевизор LG OLED55C1RLA
Стоимость товара   : 144990.0
Категория товара   : Телевизоры
ссылка на товар    : https://www.mvideo.ru/products/10026091

ID товара          : 20071813
Наименование товара: Парогенератор Braun 12810000-IS2058BK
Стоимость товара   : 9990.0
Категория товара   : Утюги
ссылка на товар    : https://www.mvideo.ru/products/20071813

ID товара          : 20071900
Наименование товара: Пылесос ручной (handstick) Tefal X-Force Flex 11.60 Aqua TY9890WO
Стоимость товара   : 31990.0
Категория товара   : Пылесосы
ссылка на товар    : https://www.mvideo.ru/products/20071900

ID товара          : 20072923
Наименование товара: Триммер Braun BS 1000
Стоимость товара   : 3290.0
Категория товара   : Триммеры
ссылка на товар    : https://www.mvideo.ru/products/20072923

ID товара          : 20072169
Наименование товара: Стайлер Rowenta Ultimate Experience Air Care CF4310F0
Стоимость товара   : 8990.0
Категория товара   : Электрощипцы
ссылка на товар    : https://www.mvideo.ru/products/20072169


Товаров в базе до импорта данных: 17
Товаров в базе после импорта: 17
Добавлено 0 товаров
"""
