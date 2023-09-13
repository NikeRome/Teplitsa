import requests
import random
import time

import socket

def get_local_ip():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address

# Получение локального IP-адреса
local_ip = get_local_ip()

# URL сервера, куда будут отправляться данные
def get_local_ip():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address


server_url = 'http://' + get_local_ip() + ':5000/'
print(server_url)
sensor_path = 'sensor'

# Эмулируем получение данных с платы Arduino
def get_sensor_data():
    temperature = random.uniform(20.0, 30.0)
    humidity = random.uniform(40.0, 60.0)
    light = random.randint(0, 100)
    return temperature, humidity, light

# Отправка данных на сервер
def send_data_to_server(temperature, humidity, light):
    params = {
        'temperature': temperature,
        'humidity': humidity,
        'light': light
    }
    response = requests.get(server_url + 'sensor', params=params)
    if response.status_code == 200:
        print('Данные успешно отправлены на сервер')
    else:
        print('Ошибка при отправке данных на сервер')

# Эмуляция работы платы Arduino и отправка данных на сервер в цикле
def emulate_arduino():
    while True:
        temperature, humidity, light = get_sensor_data()
        send_data_to_server(temperature, humidity, light)
        time.sleep(5)  # Задержка между отправками данных

# Запуск эмуляции Arduino
emulate_arduino()
