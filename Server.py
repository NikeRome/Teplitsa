import sqlite3
import datetime
import socket
import matplotlib.pyplot as plt
import io
import base64
import os
import sys
from flask import Flask, request, render_template
#
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
#
plt.switch_backend('Agg')  # Используйте не-GUI backend для Matplotlib


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

templates_path = resource_path(fr".\templates")
app = Flask(__name__, template_folder=templates_path)

# Подключение к базе данных
connection = sqlite3.connect('database.db', check_same_thread=False)
cursor = connection.cursor()

# Создание таблицы, если она еще не существует
cursor.execute('''
CREATE TABLE IF NOT EXISTS sensor_data 
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    temperature REAL,
    humidity REAL,
    light INTEGER,
    time DATETIME
)
''')
connection.commit()

last_temperature_id = 0
last_humidity_id = 0
        
def config_load(file_path):
    parameters = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

            for line in lines:
                # Пропустить строки, начинающиеся с символа #
                if line.startswith('#'):
                    continue

                # Разделить строку на ключ и значение
                key_value = line.strip().split('=')
                if len(key_value) != 2:
                    continue

                key = key_value[0].strip()
                value = key_value[1].strip()
                value = value.strip(';')

                # Пропустить пустые ключи или значения
                if not key or not value:
                    continue

                # Проверить типы данных и присвоить значения параметрам
                if key in ['Максимальная температура', 'Минимальная температура', 'Максимальная влажность', 'Минимальная влажность']:
                    try:
                        parameters[key] = float(value)
                    except ValueError:
                        print(f"Ошибка: Неверный тип данных для параметра {key}")
                elif key in ['SMTP порт', 'Порт сервера', 'Задержка отправки (в количестве измерений шт.)']:
                    try:
                        parameters[key] = int(value)
                    except ValueError:
                        print(f"Ошибка: Неверный тип данных для параметра {key}")
                else:
                    parameters[key] = value

    except FileNotFoundError:
        print("Ошибка: Файл не найден.")
        
    return parameters

file_path = input("Введите путь к файлу configs: ")
if file_path:
    parameters = config_load(file_path)

@app.route('/sensor', methods=['GET'])
def handle_get():
    # Получаем данные
    temperature = request.args.get('temperature')
    humidity = request.args.get('humidity')
    light = request.args.get('light')
    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        # Запись данных в базу данных
        cursor.execute("INSERT INTO sensor_data (temperature, humidity, light, time) VALUES (?, ?, ?, ?)",
                   (temperature, humidity, light, time))
        connection.commit()

        # Если температура превысила установленную норму
        if  not parameters['Минимальная температура'] < float(temperature) < float(parameters['Максимальная температура']):
            send_message('temp', temperature)
        if  not parameters['Минимальная влажность'] < float(humidity) < parameters['Максимальная влажность']:
            send_message('humid', humidity)

    except Exception as e:
        return f'Произошла ошибка при записи данных в базу данных: {str(e)}'

    return 'Данные успешно получены и записаны в базу данных!'

# Маршрут для отображения графика
@app.route('/graph', methods=['GET'])
def show_graph():
    # Получение данных из базы данных
    cursor.execute("SELECT time, temperature FROM sensor_data")
    temperature_rows = cursor.fetchall()
    temperature_times = []
    temperature_values = []

    for row in temperature_rows:
        temperature_times.append(row[0])
        temperature_values.append(row[1])

    cursor.execute("SELECT time, humidity FROM sensor_data")
    humidity_rows = cursor.fetchall()
    humidity_times = []
    humidity_values = []
    for row in humidity_rows:
        humidity_times.append(row[0])
        humidity_values.append(row[1])

    cursor.execute("SELECT time, light FROM sensor_data")
    light_rows = cursor.fetchall()
    light_times = []
    light_values = []
    for row in light_rows:
        light_times.append(row[0])
        light_values.append(row[1])

    # Создание графика для температуры
    plt.figure(figsize=(10, 5))
    plt.plot(temperature_times, temperature_values, label='Температура', color='red')
    plt.xlabel('Время')
    plt.ylabel('Температура')
    plt.title('График температуры')
    plt.grid()
    plt.legend()
    plt.xticks(temperature_times[::len(temperature_times)//3])

    # Преобразование графика в изображение
    temperature_img = io.BytesIO()
    plt.savefig(temperature_img, format='png')
    temperature_img.seek(0)
    temperature_plot_url = base64.b64encode(temperature_img.getvalue()).decode()

    # Создание графика для влажности
    plt.figure(figsize=(10, 5))
    plt.plot(humidity_times, humidity_values, label='Влажность', color='blue')
    plt.xlabel('Время')
    plt.ylabel('Влажность')
    plt.title('График влажности')
    plt.grid()
    plt.legend()
    plt.xticks(temperature_times[::len(temperature_times)//3])

    # Преобразование графика в изображение
    humidity_img = io.BytesIO()
    plt.savefig(humidity_img, format='png')
    humidity_img.seek(0)
    humidity_plot_url = base64.b64encode(humidity_img.getvalue()).decode()

    # Создание графика для освещения
    plt.figure(figsize=(10, 5))
    plt.plot(light_times, light_values, label='Освещённость', color='green')
    plt.xlabel('Время')
    plt.ylabel('Освещённость')
    plt.title('График освещённости')
    plt.grid()
    plt.legend()
    plt.xticks(temperature_times[::len(temperature_times)//3])

    # Преобразование графика в изображение
    light_img = io.BytesIO()
    plt.savefig(light_img, format='png')
    light_img.seek(0)
    light_plot_url = base64.b64encode(light_img.getvalue()).decode()

    connection.commit()

    return render_template('graph.html', temperature_plot=temperature_plot_url, humidity_plot=humidity_plot_url, light_plot=light_plot_url)

# Уведомление пользователя о случившихся проблемах
def send_message(param_name, param_value):
    global last_humidity_id
    global last_temperature_id
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()
    # Выполнение запроса для получения последнего id
    cursor.execute("SELECT MAX(id) FROM sensor_data")
    result = cursor.fetchone()
    # Получение значения последнего id
    current_humidity_id = int(result[0])
    current_temperature_id = int(result[0])
    
    SMTP_SERVER = parameters['SMTP сервер']
    SMTP_PORT = parameters['SMTP порт']
    SMTP_USERNAME = parameters['Логин SMTP']
    SMTP_PASSWORD = parameters['Пароль SMTP']
    
    # Создание объекта контекста SSL/TLS
    context = ssl.create_default_context()
    if (current_humidity_id - last_humidity_id >= parameters['Задержка отправки (в количестве измерений шт.)']  or last_humidity_id == 0) and param_name == 'humid':
        text_to_send = 'Влажность в теплице: '
        last_humidity_id = current_humidity_id
    elif (current_temperature_id - last_temperature_id >= parameters['Задержка отправки (в количестве измерений шт.)'] or last_temperature_id == 0) and param_name =='temp':
        text_to_send = 'Температура в теплице: '
        last_temperature_id = current_temperature_id
    else:
        return
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)

            message = MIMEMultipart()
            message['From'] = parameters['Почта отправителя']
            message['To'] = parameters['Почта получателя']
            message['Subject'] = parameters['Тема сообщения']
            
            message.attach(MIMEText(text_to_send + str(round(float(param_value),2)), 'plain'))

            server.sendmail(message['From'], message['To'], message.as_string())
            server.quit()
            print("Письмо успешно отправлено!")

    except Exception as e:
        print(f"Произошла ошибка при отправке письма: {str(e)}")

ip = parameters['IP-адрес сервера']
port = parameters['Порт сервера']


# Запуск сервера
if __name__ == '__main__':
    app.run(host=ip, port=int(port))