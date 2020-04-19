#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import json, sqlite3, os
from requests import get
from datetime import datetime
from re import findall
from time import time
from progress.bar import IncrementalBar as Bar

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) # Не на всех машинах работают запросы по HTTPS (Entware в частности), поэтому используется HTTP. Вообще, это крайне не рекомендуется из соображений безопасности.
requestHTTPSVerify = False # Если хотите использовать HTTPS, смените на True. Если выходят ошибки urllib3, попробуйте сменить на False

### Блок 0. Создание БД(при отсутствии), подключение к БД, создание функции для добавления элементов в базу по заданному формату

conn = sqlite3.connect(os.path.join(os.getcwd(), "PDB.db"))
crsr = conn.cursor()

try:
    crsr.execute("""SELECT * FROM pack WHERE pack_ID = 0""")
except sqlite3.OperationalError:
    Update = False
    count = 1 # Отсчёт для запросов к VK
    packCount = 0 # Отсчёт паков для статистики
    crsr.execute("""CREATE TABLE "pack" (
	"pack_ID"	INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
	"name"	TEXT NOT NULL,
	"publisher_ID"	INTEGER NOT NULL,
	"date"	INTEGER NOT NULL,
	"source"	TEXT NOT NULL,
	"link"	TEXT NOT NULL,
	"tags"	TEXT
    );""")
else:
    Update = True
    packCount = json.loads(crsr.execute("SELECT tags FROM pack WHERE pack_ID = 0").fetchall()[0][0])["Parsed"] # Получение количества пакетов за предыдущее обновление
    count = json.loads(crsr.execute("SELECT tags FROM pack WHERE pack_ID = 0").fetchall()[0][0])["Answers"] # Получение общего количества ответов за предыдущее обновление


def AddToBase(pack_ID, name, publisher_ID, date, source, link, tags): #name, creator.ID, date, src, link, tags
    crsr.execute("""INSERT INTO pack VALUES ({}, "{}", {}, {}, "{}", "{}", '{}');""".format(pack_ID, name, publisher_ID, date, source, link, tags))

### Блок 1. Подготовка параметров, использующихся в get-запросах.

URL_START = "https://api.vk.com/method/"
URL_METHOD = "board.getComments?" #Информация по методу - https://vk.com/dev/board.getComments
URL_PARAMS = {"v": 5.103,
              "access_token": "", # Для парсинга вам необходим токен ВК. Получить его вы можете здесь(Рекомендую использовать токен Kate Mobile): https://vkhost.github.io/
              "group_id": 135725718,
              "topic_id": 34975471,
              "offset": 1,
              "count": 100,
              "extended": 1}

if len(URL_PARAMS["access_token"]) != 85: # Проверка токена на длину. По умолчанию длина токена с максимальными правами у ВК - 85.
    raise Exception("No valid VK Token found. Please, check line #47 of code.")

### Блок 2. Получение общего количества ответов на обсуждение - [target].

URL_PARAM = []
for i in URL_PARAMS:
    URL_PARAM.append("{}={}".format(i, URL_PARAMS[i]))
URL_END = "&".join(URL_PARAM)
target = json.loads(get(URL_START + URL_METHOD + URL_END, verify = requestHTTPSVerify).text)["response"]["count"]

### Блок 3. Получение всех ответов и запись в переменную [result].


if Update or count <= target:
    if Update:
        countBar = Bar("Answers parsed\t", max = target-count)
    else:
        countBar = Bar("Answers parsed\t", max = target)
    while count <= target:
        if Update:
            URL_PARAMS["offset"] = count
        URL_PARAM = []
        for i in URL_PARAMS:
            URL_PARAM.append("{}={}".format(i, URL_PARAMS[i]))
        URL_END = "&".join(URL_PARAM)
        try:
            res = json.loads(get(URL_START + URL_METHOD + URL_END).text)["response"]["items"] #Переопределение в данном случае нужно для обновления информации. Без него, в теории, вы будете получать лишь первые 100 ответов [target/100] раз
            result += res
        except NameError:
            result = json.loads(get(URL_START + URL_METHOD + URL_END).text)["response"]["items"]
        URL_PARAMS["offset"] += 100
        count += 100
        countBar.next(100)
    countBar.finish()
elif count >= target:
    print("\nКоличество ответов в обсуждении не изменилось. Нечего получать.\n")

### Блок 4. Фильтрация ответов.




if Update:
    baseAddBar = Bar("Answers processed\t", max = target-count)
else:
    baseAddBar = Bar("Answers processed\t", max = target)
for i in result:
    try:
        i["attachments"] # Попытка получить прикреплённые документы
    except KeyError: # Поиск ссылок на сторонние ресурсы в случае отсутствия прикреплённых документов. Легче всего получать паки с помощью API, однако ни гугл, ни яндекс не дают доступ к API без авторизации. Данная проблема решена парсингом веб-страницы с пакетом
        if i["text"].find("yadi.sk") > -1: #Получение ссылок c ЯД
            if i["text"].find("\n") > -1 or i["text"].find(" ") > -1: # Фильтрация на наличие пробелов и переносов строки. На случай, если ссылок будет больше, чем 1
                tempList = findall("yadi.sk/d/[\w\-]*", i["text"])
                for t in tempList:
                    try:
                        a = findall("""<div class="file-name">[\w ]+.\w+</div>""", get("https://" + t).text)[0]
                    except IndexError:
                        pass
                    else:
                        try:
                            i["owner_id"]
                        except Exception:
                            pass
                        else:
                            packCount += 1
                            name = a[23:len(a)-6] # Получение названия документа исходя из разметки веб-страницы. Получено опытным путём; при обновлении ресурсов, где хранятся паки, может не сработать.
                            AddToBase(packCount, # Последовательный номер пакета в базе
                                      name, # Название документа
                                      i['from_id'], # ID пользователя ВК, опубликовавшего пакет
                                      i["date"], # Для получения стандартного времени(ДД.ММ.ГГГГ ЧЧ:ММ:СС) вместо эпохи Unix, используйте конструкцию datetime.utcfromtimestamp(i["date"]).strftime('%d.%m.%Y %H:%M:%S')
                                      "Yandex.Disk", # В принципе, для оптимизации базы можно убрать поле источника базы. Лично я считаю, что это важно для статистики, но саму статистику я веду лишь на будущее.
                                      t, # Ссылка на документ
                                      "") # Пустое поле для тегов. Можно использовать в качестве тегов фильтр по названию, а можно вытаскивать темы из пака - файлы .siq представляют из себя простые архивы, а содержимое пака регулируется файлом context.xml, где хранятся названия раундов и категорий. Фильтруя названия категорий, можно получить полноценное тегирование, но для этого нужно качать пак целиком. Решение данной проблемы на 25.03.2020 не найдено
        elif i["text"].find("drive.google") != -1: # Получение ссылок с Google Drive. Конструкция аналогична получению ссылок с ЯД
            if i["text"].find("\n") > -1 or i["text"].find(" ") > -1:
                tempList = findall("drive.google.com/open?id=[\w\-]*", i["text"])
                if len(tempList) == 0:
                    tempList = findall("drive.google.com/file/d/[\w\-]*", i["text"])
                for t in tempList:
                    try:
                        a = findall("""<meta property="og:title" content="\w+.\w+">""", get("https://" + t).text)[0]
                    except IndexError:
                        pass
                    else:
                        packCount += 1
                        name = a[35:len(a)-2]
                        AddToBase(packCount,
                                  name,
                                  i['from_id'],
                                  i["date"],
                                  "Google Drive",
                                  t,
                                  "")
    else:
        for j in i["attachments"]:
            try:
                file = j["doc"] # Попытка получить список документов
            except KeyError:
                pass # Действие при отсутствии документов
            else:
                if file["ext"] == "siq": # Проверка документа на необходимое расширение
                    packCount += 1
                    if file['title'].find('.siq') == -1:
                        file['title'] += '.siq'
                    try:
                        AddToBase(packCount,
                                  file['title'],
                                  file['owner_id'],
                                  file["date"],
                                  "VK",
                                  file['url'],
                                  "")
                    except Exception as error:
                        print(file + "\n" + error)
                else:
                    pass
    baseAddBar.next()
baseAddBar.finish()

# Окончание работы, сохранение и вывод статистики

if Update:
    tags = json.loads(crsr.execute("SELECT tags FROM pack WHERE pack_ID = 0").fetchall()[0][0])
    tags["Parsed"] = packCount
    tags["Answers"] = target
    crsr.execute("""UPDATE pack SET tags = '{}', date = {} WHERE pack_ID = 0;""".format(json.dumps(tags), round(time()))) # Обновление информации о положении базы
else:
    tags = json.loads("""{"Parsed": 0,"Answers": 0}""")
    tags["Parsed"] = packCount
    tags["Answers"] = target
    AddToBase(0, "INFO", 257018408, round(time()), "SIPP", "", json.dumps(tags)) # Добавление информации о текущем положении базы в качестве нулевого элемента при отсутствии таковой. Используется для обновления базы вместо полного получения всех паков заново
conn.commit()
conn.close()
print("В базе теперь [{}] паков. Общее количество ответов: {}".format(packCount, target))
