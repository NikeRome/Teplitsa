Программа реализует создание сервера с помощью библиотеки Flask, на который приходят данные от датчиков (Arduino), и программа считывает их с помощью get запросов. 
Для настроек параметров, сервера и SMTP предусмотрено считывание входных данных из файла формата txt. 

После запуска сервера с указанными настройками программа начинает получать данные с сервера и записывать их в базу данных SQLite.

Если показатели слишком низкие или слишком высокие, то программа отправляет предупреждение на указанную электронную почту. Чтобы сообщений не было слишком много создано ограничение на отправку.
Оно работает по следующему принципу: если это первое за текущий запуск сервера оповещение, то оно будет отправлено в любом случае.
Если это не первое сообщение и с момента последнего сообщения прошло не менее 8 (количество указывается в параметрах) полученных с сервера сообщений с данными, то письмо отправляется.

На сервере куда поступают данные также происходит отрисовка графиков показателей во времени для визуального определения закономерностей.
В программу вшит шаблон html страницы для графиков. Доступ к графикам осуществляется с помощью введённого в configs.txt ip-адреса и порта с маршрутом /graph.