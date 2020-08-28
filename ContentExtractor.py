#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import zipfile, os, xmltodict, json, sqlite3
from uuid import uuid4

path = os.getcwd()

conn = sqlite3.connect(os.path.join(path, "PDB.db"))
crsr = conn.cursor()
packLimit = json.loads(crsr.execute("""SELECT tags FROM pack WHERE pack_ID = 0""").fetchall()[0][0])["Parsed"]

# Извлечение конкретного контекста для использования ботом

def getContent(packNum):
    packRealName = crsr.execute("""SELECT name FROM pack WHERE pack_ID = {}""".format(packNum)).fetchall()[0][0]
    packName = str(packNum) + '. ' + packRealName
    if (
        packNum > 0 
    and packNum <= int(packLimit) 
    and crsr.execute("""SELECT source FROM pack WHERE pack_ID = {}""".format(packNum)).fetchall()[0][0] == "VK" 
    and zipfile.is_zipfile(os.path.join(path, 'Packs', packName))):
        packContentUUID = str(uuid4())
        pack = zipfile.ZipFile(
            os.path.join(path, 'Packs', packName)
        )
        pack.extract("content.xml", os.path.join(path, 'temp'))
        os.rename(
            os.path.join(path, 'temp', 'content.xml'), 
            os.path.join(path, "temp", "{}.xml".format(packContentUUID))
            )
        packDict = json.loads(
            json.dumps(
                xmltodict.parse(
                    open(
                            os.path.join(path, "temp", "{}.xml".format(packContentUUID))
                        ).read()
                )
            )
        )["package"]
        os.remove(os.path.join(path, 'temp', '{}.xml'.format(packContentUUID)))
        packStructure = "Пакет: {0}\nАвтор: {1}\n".format(packRealName, packDict["info"]["authors"]["author"])
        if len(packDict['rounds']) == 1 and len(packDict['rounds']['round']) == 2:
            packStructure += "\n=Раунд: {}\n".format(packDict['rounds']['round']["@name"])
            for theme in packDict['rounds']['round']["themes"]["theme"]:
                packStructure += "===Тема: {}\n".format(theme["@name"])
        else:
            for round in packDict["rounds"]["round"]:
                packStructure += "\n=Раунд: {}\n".format(round["@name"])
                for theme in round["themes"]["theme"]:
                    packStructure += "===Тема: {}\n".format(theme["@name"])
    else:
        packStructure = "Error: Unable to read context file."
    return packStructure

# Извлечение всех контекстов

def extractContexts():
    for i in os.listdir('../PackDownloader'):
        if zipfile.is_zipfile("../PackDownloader/{}".format(i)):
            target = zipfile.ZipFile("../PackDownloader/{}".format(i))
            target.extract("content.xml")
            os.rename("content.xml", "{}.xml".format(i))

# Создание архива со всеми контекстами имеющихся паков

def getOverallContexts():
    z = zipfile.ZipFile('../contexts.zip', mode = 'w')
    for file in os.listdir():
        if file.find("xml") > -1:
           z.write(file)
    z.close()

# Получение информации о работе

def getZeroTags():
    res = ''
    tags = json.loads(crsr.execute("SELECT tags FROM pack WHERE pack_ID=0").fetchall()[0][0])
    for i in tags:
        res += "{}: {}\n".format(i, tags[i])
    return res
