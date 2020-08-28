#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import sqlite3, json
from urllib.request import urlretrieve
from time import time
from datetime import datetime
from os import path, getcwd, pardir, mkdir

def convert(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%d:%02d:%02d" % (hour, minutes, seconds)

conn = sqlite3.connect( path.join(getcwd(), "PDB.db") )
crsr = conn.cursor()
target = json.loads(crsr.execute( "SELECT tags FROM pack WHERE pack_ID = 0" ).fetchall()[0][0])["Parsed"] 

downloadDir = "Packs" # Название папки для загрузки паков
if path.exists( path.join(getcwd(), downloadDir) ): # Проверка наличия папки с таким названием. Можно реализовать через try, т.к. mkdir при наличии папки просто выдаёт ошибку
    pass
else:
    mkdir( path.join(getcwd(), downloadDir) )

print("Скрипт запущен. Время: " + datetime.utcfromtimestamp(int(time()) + 3600*3).strftime( '%d.%m.%Y %H:%M:%S' ))

packs = crsr.execute("""SELECT link, pack_ID, name, source, isDownloaded FROM pack WHERE pack_ID > 0""").fetchall()
oldTime = round(time())
startTime = round(time())

for pack in packs:
    if pack[4] == False:
        if pack[3] == "VK":
            packName = "{}. {}".format(
                                        pack[1], 
                                        pack[2]
                                            .replace("/", " ") # Все эти знаки запрещены в названии файла в ОС Windows
                                            .replace(":", " ") # При необходимости это всё можно просто закомментировать
                                            .replace("\\", " ")
                                            .replace("|", " ")
                                            .replace("*", " ")
                                            .replace('"', " ")
                                            .replace("<", " ")
                                            .replace(">", " ")
                                        )
            if packName.find(".siq") == -1: # Не у всех паков есть расширение в имени, поэтому необходима эта проверка
                packName += ".siq"          # И добавление соответствующего расширения по необходимости
            urlretrieve(pack[0], path.join(getcwd(), downloadDir, packName)) # Загрузка пака
            print("[{1}] Получен пак №{0}. Прошло с прошлого - {2},с начала - {3}".format( # Вывод информации по времени после загрузки пака
                                                                                            pack[1], 
                                                                                            datetime.utcfromtimestamp( int(time()) + 3600*3 ).strftime('%d.%m.%Y %H:%M:%S'), 
                                                                                            convert(int(time()) - oldTime), 
                                                                                            convert(int(time()) - startTime)
                                                                                        )
                )
            oldTime = time() 
            if path.exists(path.join(getcwd(), downloadDir, packName)): # Проверка наличия пака в папке
                crsr.execute("UPDATE pack SET isDownloaded=1 WHERE pack_ID = {}".format( pack[1] )) # Пометка файла как загруженного в случае наличия
            else:
                crsr.execute("UPDATE pack SET isDownloaded=0 WHERE pack_ID = {}".format( pack[1] )) # Пометка файла как незагруженного в случае отсутствия
            conn.commit()
    else:
        print("[{1}] Пак №{0} был загружен одной из предыдущих итераций.".format(
                                                            pack[1], 
                                                            datetime.utcfromtimestamp( int(time()) + 3600*3 ).strftime( '%d.%m.%Y %H:%M:%S' )
                                                        )
    )

conn.close()
print("That's all, folks!") # Уведомление об окончании работы скрипта
