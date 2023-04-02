import requests
import folium
import subprocess
import re
import os

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from config import TOKEN

from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext


class Form(StatesGroup):
    ip = State()
    traicing = State()


def get_info(ip) -> dict:
    try:
        response = requests.get(url=f'http://ip-api.com/json/{ip}').json()
        data = {
            'ip': response.get('query'),
            'org': response.get('org'),
            'city': response.get('city'),
            'country': response.get('country'),
            'lat': response.get('lat'),
            'lon': response.get('lon')
        }
        return data

    except requests.exceptions.ConnectionError:
        print('Please check your connection!')


def create_route_map(ips: [str], url: str) -> str:
    if url[0].isdigit():
        url_name = ""  # ip address
    else:
        url_name = re.search("[a-z]*\.([a-zA-Z]+)\.[a-z]+", url)  # url address
        if url_name:
            url_name = url_name.group(1)
        else:
            url_name = re.search("([a-zA-Z]+)\.[a-z]+", url)  # url address
            if url_name:
                url_name = url_name.group(1)
            else:
                return ""

    loc = []
    createdmap = False
    for id_, ip in enumerate(ips):
        try:
            response = requests.get(url=f'http://ip-api.com/json/{ip}').json()
            data = {
                'ip': response.get('query'),
                'org': response.get('org'),
                'city': response.get('city'),
                'country': response.get('country'),
                'lat': response.get('lat'),
                'lon': response.get('lon')
            }

            print(data['city'])

            latitude = response.get('lat')
            longitude = response.get('lon')
            loc.append((latitude, longitude))

            if not createdmap:
                area = folium.Map(location=[latitude, longitude])
                createdmap = True

            popup = "<i>{} server #{}</i>".format(data['org'], id_)
            folium.Marker(
                [latitude, longitude], popup=popup
            ).add_to(area)

        except requests.exceptions.ConnectionError:
            print('Please check your connection!')
            return ""

    if url[0].isdigit():
        url_name = data['org']
    folium.PolyLine(loc).add_to(area)
    area.save(f'{url_name}.html')
    return f'{url_name}.html'


bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)


@dp.message_handler(commands=["get_ip_info"], state=None)
async def ip_info(message: types.Message):
    await message.answer("Enter ip to search")
    await Form.ip.set()


@dp.message_handler(state=Form.ip)
async def handle_ip_info(message: types.Message, state: FSMContext):
    data = get_info(message.text)
    await message.answer(f'IP Info\nOwner: {data["org"]}\nCity: {data["city"]}\nCountry: {data["country"]}')
    await state.finish()


@dp.message_handler(commands=["traicing"])
async def initiate_tracing(message: types.Message):
    await message.answer("Enter IP or URL to trace route")
    await Form.traicing.set()


@dp.message_handler(state=Form.traicing)
@dp.message_handler(regexp='[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}')
@dp.message_handler(regexp='[a-z]*\.[a-zA-Z]+\.[a-z]+|[a-zA-Z]+\.[a-z]+')
async def tracing(message: types.Message, state: FSMContext):
    url = str(message.text)
    await message.answer(f'Ok, tracing to {message.text}, please wait...')
    out = subprocess.check_output(["traceroute", "-w", "3", url])
    all_ips = re.findall("\(([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\)", str(out))
    all_ips = all_ips[1:]
    filename = create_route_map(all_ips, url)
    if filename:
        await message.answer_document(open(filename, 'r'))
        os.remove(filename)
    else:
        await message.answer(f'Something went wrong, please check address')

    await state.finish()


def main():
    executor.start_polling(dp, skip_updates=True)


if __name__ == '__main__':
    main()
