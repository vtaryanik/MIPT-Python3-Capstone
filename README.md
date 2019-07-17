# MIPT-Python3-Capstone
## 1. Client

Если вы разрабатываете настоящий проект, у которого есть большое количество пользователей, то необходимо наблюдать за всеми процессами, происходящими в нем. Для этого нужно смотреть за численными показателями в проекте. Показатели могут быть самыми разными - количество запросов к вашему приложению, время ответа вашего сервиса на каждый запрос, количество пользователей в сутки, и т.д. Эти всевозможные численные показатели мы будем называть метриками.

Для сбора, хранения и отображения подобных метрик существуют готовые решения, например Graphite, InfluxDB. Мы в рамках курса разработаем свою систему для сбора метрик - сервер и клиент.

Протокол взаимодействия
Клиент и сервер должны взаимодействовать между собой по простому текстовому протоколу через TCP сокеты. 
Необходимо реализовать две команды:

put - для сохранения метрик на сервере.
get - для получения метрик.

Формат команды put для отправки метрик — это строка вида: put <key> <value> <timestamp>\n
Успешный ответ от сервера: ok\n\n
Ошибка сервера: error\nwrong command\n\n

Формат команды get для получения метрик — это строка вида: get <key>\n
В качестве ключа можно указывать символ *, для этого символа будут возвращены все доступные метрики.

Реализация клиента.
Необходимо реализовать класс Client, в котором будет инкапсулировано соединение с сервером, клиентский сокет и методы для получения и отправки метрик на сервер. В конструктор класса Client должна передаваться адресная пара хост и порт, а также необязательный аргумент timeout (timeout=None по умолчанию). У класса Client должно быть 2 метода: put и get, соответствующих протоколу выше.

Клиент получает данные в текстовом виде, метод get должен возвращать словарь с полученными ключами с сервера. Значением ключа в словаре является список кортежей [(timestamp, metric_value), ...], отсортированный по timestamp от меньшего к большему. Значение timestamp должно быть преобразовано к целому числу int. Значение метрики metric_value нужно преобразовать к числу с плавающей точкой float.

Метод put принимает первым аргументом название метрики, вторым численное значение, третьим - необязательный именованный аргумент timestamp. Если пользователь вызвал метод put без аргумента timestamp, то клиент автоматически должен подставить текущее время в команду put - str(int(time.time()))

Метод put не возвращает ничего в случае успешной отправки и выбрасывает исключение ClientError в случае неуспешной.

Метод get принимает первым аргументом имя метрики, значения которой мы хотим выгрузить. Также вместо имени метрики можно использовать символ *, о котором говорилось в описании протокола.

Метод get возвращает словарь с метриками (смотрите ниже пример) в случае успешного получения ответа от сервера и выбрасывает исключение ClientError в случае неуспешного.


