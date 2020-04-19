#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import sqlite3, json
from urllib.request import urlretrieve
from time import time
from datetime import datetime
from os import path

def convert(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%d:%02d:%02d" % (hour, minutes, seconds)

conn = sqlite3.connect("/disk/SIGame/PDB.db")
crsr = conn.cursor()
tags = json.loads(crsr.execute("SELECT tags FROM pack WHERE pack_ID = 0").fetchall()[0][0])

try:
    tags["Downloaded"]
except IndexError:
    tags.append("0")

if tags["Downloaded"] == tags["Parsed"]:
    print("Новых паков нет. Вырубаемся...")
else:
    packs = crsr.execute("""SELECT link, pack_ID, name, src FROM pack WHERE pack_id > {}""".format(tags["Downloaded"])).fetchall()
    print("Скрипт запущен. Время: " + datetime.utcfromtimestamp(int(time()) + 3600*3).strftime('%d.%m.%Y %H:%M:%S'))
    oldtime = time()
    starttime = time()

    for pack in packs:
        if pack[3] == "VK":
            packName = "{}-{}".format(pack[1], pack[2].replace("/", " "))
            if packName.find(".siq") == -1:
                packName += ".siq"
            urlretrieve(pack[0], path.join("/disk/SIGame/Packs", packName))
            print("[{1}]Получен пак №{0}. Прошло с прошлого - {2},с начала - {3}".format(pack[1], datetime.utcfromtimestamp(int(time()) + 3600*3).strftime('%d.%m.%Y %H:%M:%S'), convert(round(int(time()) - oldtime)), convert(round(int(time()) - starttime))))
            oldtime = time()
            tags["Downloaded"] = pack[1]
            crsr.execute("UPDATE pack SET tags = '{}' WHERE pack_ID = 0".format(json.dumps(tags)))
            conn.commit()
            if path.exists("/disk/SIGame/Packs/{}".format(packName)):
                crsr.execute("UPDATE pack SET isDownloaded=1, isDeleted=0 WHERE pack_ID = {}".format(pack[1]))
            else:
                crsr.execute("UPDATE pack SET isDownloaded=0 WHERE pack_ID = {}".format(pack[1]))
    conn.close()
    print("That's all, folks!")
