"""
Задание 2.
Изучить список открытых API. Найти среди них любое, требующее авторизацию (любого типа).
Выполнить запросы к нему, пройдя авторизацию. Ответ сервера записать в файл.
"""

import requests
import json
from pprint import pprint

link = "https://api.nasa.gov/planetary/apod"
api_key = ''
params = {'api_key': api_key}

response = requests.get(link, params=params)

if response.ok:
    data = response.json()

    with open('nasa_apod.json', 'w') as f:
        json_to_file = json.dump(data, f, indent=4)

    with open('nasa_apod.json', 'r') as f:
        json_from_file = json.load(f)

    info = data['explanation']
    print(f"Дата актуализации: {data['date']}\nИзображение 1: {data['hdurl']}\n"
          f"Изображение 2: {data['url']})")
    string = ''
    print('Информация по снимкам:')
    for i in range(len(info)):
        string += info[i]
        if len(string) % 70 == 0:
            print(string)
            string = ''
    print(string)

    print(f'\nВыгрузка из файла:')
    pprint(json_from_file)

"""
Результат:

Дата актуализации: 2021-04-08
Изображение 1: https://apod.nasa.gov/apod/image/2104/PIA24547_fig1.jpg
Изображение 2: https://apod.nasa.gov/apod/image/2104/PIA24547_fig1_1024.jpg)
Информация по снимкам:
The multicolor, stereo imaging Mastcam-Z on the Perseverance rover zoo
med in to captured this 3D close-up (get out your red/blue glasses) of
 the Mars Ingenuity helicopter on mission sol 45, April 5. That's only
 a few sols before the technology demonstrating Ingenuity will attempt
 to fly in the thin martian atmosphere, making the first powered fligh
t on another planet. The historic test flight is planned for no earlie
r than Sunday, April 11.  Casting its shadow on the martian surface, I
ngenuity is standing alone on four landing legs next to the rover's wh
eel tracks. The experimental helicopter's solar panel, charging batter
ies that keep it warm through the cold martian nights and power its fl
ight, sits above its two 1.2 meter (4 foot) long counter-rotating blad
es.

Выгрузка из файла:
{'date': '2021-04-08',
 'explanation': 'The multicolor, stereo imaging Mastcam-Z on the Perseverance '
                'rover zoomed in to captured this 3D close-up (get out your '
                'red/blue glasses) of the Mars Ingenuity helicopter on mission '
                "sol 45, April 5. That's only a few sols before the technology "
                'demonstrating Ingenuity will attempt to fly in the thin '
                'martian atmosphere, making the first powered flight on '
                'another planet. The historic test flight is planned for no '
                'earlier than Sunday, April 11.  Casting its shadow on the '
                'martian surface, Ingenuity is standing alone on four landing '
                "legs next to the rover's wheel tracks. The experimental "
                "helicopter's solar panel, charging batteries that keep it "
                'warm through the cold martian nights and power its flight, '
                'sits above its two 1.2 meter (4 foot) long counter-rotating '
                'blades.',
 'hdurl': 'https://apod.nasa.gov/apod/image/2104/PIA24547_fig1.jpg',
 'media_type': 'image',
 'service_version': 'v1',
 'title': '3D Ingenuity',
 'url': 'https://apod.nasa.gov/apod/image/2104/PIA24547_fig1_1024.jpg'}

Process finished with exit code 0

"""