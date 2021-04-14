"""
Необходимо собрать информацию о вакансиях на вводимую должность (используем input или через аргументы) с сайтов
 Superjob и HH. Приложение должно анализировать несколько страниц сайта (также вводим через input или аргументы).
  Получившийся список должен содержать в себе минимум:
* Наименование вакансии.
* Предлагаемую зарплату (отдельно минимальную, максимальную и валюту).
* Ссылку на саму вакансию.
* Сайт, откуда собрана вакансия.

По желанию можно добавить ещё параметры вакансии (например, работодателя и расположение).
Структура должна быть одинаковая для вакансий с обоих сайтов. Общий результат можно вывести с помощью
dataFrame через pandas.

"""
from bs4 import BeautifulSoup as bs
import requests
import json
from pprint import pprint
import pandas as pd

url_1 = 'https://russia.superjob.ru'
url_2 = 'https://hh.ru/'

profession = input('Введите интересующую вакансию: ')

params = {'keywords': profession,
          'page': 1}
headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
                         ' (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36'}

response = requests.get(url_1 + '/vacancy/search/', params=params, headers=headers)
dom = bs(response.text, 'html.parser')

# Находим количество страниц с вакансиями на SuperJob
pages_1 = dom.find_all('span', {'class': '_1BOkc'})
sj_pages = 0
for page in pages_1:
    value = str(page.getText())
    if value.isdigit():
        sj_pages = int(value)

# Функция получения информации с сайта hh.ru и привдения ее к формату json
def getPage(page=0):
    params_2 = {
        'text': f'NAME:{profession}',
        'area': 113,  # Поиск по всей России
        'page': page,
        'per_page': 20
    }

    req = requests.get('https://api.hh.ru/vacancies', params_2)
    data = req.content.decode()
    data = json.loads(data)
    req.close()
    return data

# Функция для определения и форматирования информации по ЗП на SuperJob
def salary(s):

    if s == 'По договорённости':
        return None, None, None

    sal = s.split(" ")
    sal_final = []

    for i in range(len(sal)):
        if sal[i] != '':
            sal_final.append(sal[i])

    if sal_final[0] == 'от':
        return sal_final[1], None, sal_final[2]
    elif sal_final[0] == 'до':
        return None, int(sal_final[1]), sal_final[2]
    else:
        if len(sal_final) == 3:
            return int(sal_final[0]), int(sal_final[1]), sal_final[2]
        elif len(sal_final) == 2:
            return int(sal_final[0]), int(sal_final[0]), sal_final[1]
        else:
            return print(f'Аларм! Проблема в описании оплаты! - {s}')

# Функция для определения и форматирования информации по ЗП на HH
def salary_hh(s):

    if s == None:
        return None, None, None

    if s['currency'] == 'RUR':
        s['currency'] = 'руб.'

    if s != None:
        return int(s['from']) if s['from'] != None else s['from'], int(s['to']) if s['to'] != None else s['to'], s['currency']
    else:
        return print(f'Аларм! Проблема в описании оплаты! - {s}')

# Создаем DataFrame для хранения данных по вакансиям
vacancies = pd.DataFrame({'site': [], 'name': [], 'min_wage': [], 'max_wage': [], 'currency': [], 'link': []})

# Подсчет и вывод информации по количеству найденных страниц
print(f'Ищем данные по вакансии "{profession}", найдено страниц:\nНа SuperJob: ', end='')
sj_pages = sj_pages if sj_pages >= 1 else sj_pages + 1
print(sj_pages)

elements = getPage(0)
hh_pages = elements["pages"]

print(f'На HeadHunter: ', end='')
print(f'{hh_pages}\n{"*" * 50}')

# Обработка ввода количества страниц для скраппинга
while True:
    try:
        n = int(input(f'Введите количество страниц для сбора данных с SuperJob\n'
                              f'Досупно {sj_pages}. На каждой странице размещено по 20 ваканстий: '))
        if n < 1 or n > sj_pages:
            raise Exception
        while True:
            try:
                m = int(input(f'Введите количество страниц для сбора данных с HeadHunter\n'
                              f'Досупно {hh_pages}. На каждой странице размещено по 20 ваканстий: '))
                if m < 1 or m > hh_pages:
                    raise Exception
                print(f'{"*" * 50}\nСобираем данные с {n} страниц сайта SuperJob\n'
                      f'и с {m} страниц с сайта HeadHunter...\n{"*" * 50}\n')
                break
            except ValueError:
                print('Неверный формат данных!')
            except Exception:
                print(f'Число должно быть от 1 до {hh_pages} включительно!')
        break
    except ValueError:
        print('Неверный формат данных!')
    except Exception:
        print(f'Число должно быть от 1 до {sj_pages} включительно!')

# Переменные для хранения данных по зарплате
min = 0
max = 0
curr = ''

# Обработка данных с HeadHunter
for p in range(m):
    elements = getPage(p)
    for i in range(len(elements['items'])):
        # pprint(elements['items'][i]['name'])
        # pprint(elements['items'][i]['alternate_url'])
        min = salary_hh(elements['items'][i]['salary'])[0]
        max = salary_hh(elements['items'][i]['salary'])[1]
        curr = salary_hh(elements['items'][i]['salary'])[2]
        # print(min, max, curr)

        # Вносим данные в DataFame
        df_row = {'site': url_2, 'name': elements['items'][i]['name'], 'min_wage': min,
                  'max_wage': max, 'currency': curr, 'link': elements['items'][i]['alternate_url']}
        vacancies = vacancies.append(df_row, ignore_index=True)

# Обработка данных с SuperJob
for i in range(n):

    profession_list_1 = dom.find_all('div', {'class': 'jNMYr GPKTZ _1tH7S'})  # , limit=10

    # Выводим данные по профессиям
    for profession in profession_list_1:
        profession_name = ''
        profession_salary = ''

        profession_info_1 = profession.find('a')

        # Выводим название профессии
        profession_name_1 = profession_info_1.children
        for el in profession_name_1:
            profession_name += str(el).replace('<span class="_1rS-s">', '').replace('</span>', '')
        # pprint(profession_name)

        # Выводим ссылку на профкссию
        serial_link_1 = url_1 + profession_info_1['href']
        # pprint(serial_link_1)

        # Выводим информацию по заработной плате
        profession_salary_1 = profession.find('span', {'class': '_3mfro _2Wp8I PlM3e _2JVkc _2VHxz'}).getText()

        profession_salary = profession_salary_1.replace('\xa0', '').replace("от", "от ").replace('до', 'до ')\
                .replace('руб', ' руб').replace('—', ' ').replace('/месяц', '').replace('до г', 'дог')

        min = salary(profession_salary)[0]
        max = salary(profession_salary)[1]
        curr = salary(profession_salary)[2]
        # print(min, max, curr)

        # Вносим данные в дата фрейм
        df_row = {'site': url_1, 'name': profession_name, 'min_wage': min,
                  'max_wage': max, 'currency': curr, 'link': serial_link_1}
        vacancies = vacancies.append(df_row, ignore_index=True)

    params['page'] += 1
    response = requests.get(url_1 + '/vacancy/search/', params=params, headers=headers)
    dom = bs(response.text, 'html.parser')

print(f'Информация собрана по {vacancies.shape[0]} вакансиям.')

# Сохраняем данные из DF в файл
vacancies.to_csv('vac_list.csv')
print(f'Данные из DataFrame сохранены в файл "vac_list.csv"\n')

pprint(vacancies.head())

"""
Результат:

Введите интересующую вакансию: Data Scientist
Ищем данные по вакансии "Data Scientist", найдено страниц:
На SuperJob: 1
На HeadHunter: 23
**************************************************
Введите количество страниц для сбора данных с SuperJob
Досупно 1. На каждой странице размещено по 20 ваканстий: 1
Введите количество страниц для сбора данных с HeadHunter
Досупно 23. На каждой странице размещено по 20 ваканстий: 10
**************************************************
Собираем данные с 1 страниц сайта SuperJob
и с 10 страниц с сайта HeadHunter...
**************************************************

Информация собрана по 209 вакансиям.
Данные из DataFrame сохранены в файл "vac_list.csv"

             site  ...                            link
0  https://hh.ru/  ...  https://hh.ru/vacancy/43422264
1  https://hh.ru/  ...  https://hh.ru/vacancy/43825932
2  https://hh.ru/  ...  https://hh.ru/vacancy/43608616
3  https://hh.ru/  ...  https://hh.ru/vacancy/43289932
4  https://hh.ru/  ...  https://hh.ru/vacancy/43236923

[5 rows x 6 columns]

"""
