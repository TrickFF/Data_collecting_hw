"""
Step 2.
В данном модуле производится выгрузка данных из DF в базу
"""

from pymongo import MongoClient
from pprint import pprint
import pandas as pd

client = MongoClient('127.0.0.1', 27017)

db = client['hh_sj_scrapping'] # указатель на базу

vacancies = db.vacancies # Коллекция базы

df = pd.read_csv('vac_list.csv', index_col=[0, 1], skipinitialspace=True)

# Очистка всей коллекции
# vacancies.delete_many({})

pprint(f'Вакансий в базе до импорта данных: {db.vacancies.estimated_document_count()}')
count_1 = db.vacancies.estimated_document_count()

df.reset_index(inplace=True)
data_dict = df.to_dict("records")

# Обновляем инфу по имеющимся записям и добавляем новые (upsert=True)
for rec in data_dict:
    vacancies.update_one({'_id': rec['_id']}, {'$set': rec}, upsert=True)


pprint(f'Всего вакансий в базе после импорта: {db.vacancies.estimated_document_count()}')
pprint(f'Итого импортировано {db.vacancies.estimated_document_count() - count_1} новых записей')

"""
Результат:

'Вакансий в базе до импорта данных: 100'
'Всего вакансий в базе после импорта: 100'
'Итого импортировано: 0 новых записей'
"""
