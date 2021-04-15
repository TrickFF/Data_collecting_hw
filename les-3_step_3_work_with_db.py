"""
Step 3.
В данном модуле производится поиск и вывод данных
"""

from pymongo import MongoClient
from pprint import pprint

client = MongoClient('127.0.0.1', 27017)

db = client['hh_sj_scrapping'] # указатель на базу

vacancies = db.vacancies # Коллекция базы

# Обработка ввода даннох по ЗП
while True:
    try:
        salary = int(input(f'Введите интересующую заработную плату: '))
        if salary < 1:
            raise Exception
        break
    except ValueError:
        print('Неверный формат данных!')
    except Exception:
        print(f'Число должно быть положительным!')

# поиск вакансий по ЗП
counter = 0
for users in vacancies.find({'$or': [{'min_wage': {'$gte': salary}}, {'max_wage': {'$gte': salary}}]},
                            {'name': 1, 'min_wage': 1, 'max_wage': 1, 'link': 1, '_id': 0}):
    pprint((users))
    counter += 1

print(f'{"*" * 50}\nВакансий в базе: {db.vacancies.estimated_document_count()}')
print(f'Всего подходящих вакансий: {counter}\n{"*" * 50}')

"""
Результат:

Введите интересующую заработную плату: 250000
{'link': 'https://hh.ru/vacancy/39388485',
 'max_wage': 350000.0,
 'min_wage': 250000.0,
 'name': 'Senior Python Backend Developer (Machine Learning)'}
{'link': 'https://hh.ru/vacancy/43377259',
 'max_wage': 250000.0,
 'min_wage': 200000.0,
 'name': 'Senior Python Developer'}
{'link': 'https://hh.ru/vacancy/43729892',
 'max_wage': 400000.0,
 'min_wage': 200000.0,
 'name': 'Python разработчик (Middle+/Senior)'}
{'link': 'https://russia.superjob.ru/vakansii/senior-python-developer-36391472.html',
 'max_wage': nan,
 'min_wage': 250000.0,
 'name': 'Senior Python Developer'}
**************************************************
Вакансий в базе: 100
Всего подходящих вакансий: 4
**************************************************
"""
