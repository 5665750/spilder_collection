# -*- coding: utf-8 -*-
import requests;
from bs4 import BeautifulSoup
from queue import Queue
import sys, time, threading, os, sqlite3, json, re

header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36",
    "Referer": "http://www.girlimg.com/images/0"
}
IMAGE_URL = "http://www.girlimg.com/api/images/{0}"
CDN_URL = "http://cdn.girlimg.com/images/{0}"
TOTAL_COUNT = 0
PAGE_SIZE = 0


def initDb():
    print("初始化db")
    connection = sqlite3.connect("girlimg.db")
    # 懒得建关联表
    connection.execute("CREATE TABLE IF NOT EXISTS imgs(id INTEGER PRIMARY KEY   AUTOINCREMENT,"
                       "url TEXT,img_name TEXT,tag TEXT,flag INTEGER DEFAULT 0)")


def doGetRequest(url, stream=False,timeout=10):
    try:
        response = requests.get(url, stream=stream, headers=header,timeout=timeout)
        response.encoding = 'UTF-8'
        if (response.status_code == 200 and response):
            return response;
    except Exception as e:
        print(e)
    return None


def getTotalSize():
    global TOTAL_COUNT, PAGE_SIZE
    response = doGetRequest(IMAGE_URL.format(0))
    if (response):
        jsonStr = json.loads(response.text)
        list = jsonStr['list']
        TOTAL_COUNT = jsonStr['count']
        PAGE_SIZE = len(list)
        print("获取信息成功,总记录数{0}.每页条数{1}".format(TOTAL_COUNT, PAGE_SIZE))


def doDownLoad(imageurl, name, tag=""):
    flag = -1
    print("开始下载文件{0},标签{1}".format(name, tag))
    target_file = os.path.join(TARGET_FOLDER, name)
    if(os.path.isfile(target_file)):
        return
    response = doGetRequest(imageurl)
    if response:

        with open(target_file, 'wb') as f:
            f.write(response.content)
        flag = 1
    print("下载文件结束flag={0}".format(tag))
    connection.execute(
        "insert into imgs(url,img_name,tag,flag)  VALUEs ('{0}','{1}','{2}',{3});".format(imageurl, name, tag, flag))
    pass


def doParseWork(page):
    url = IMAGE_URL.format(page)
    response = doGetRequest(url)
    if (response):
        jsonStr = json.loads(response.text)
        list = jsonStr['list']
        for img in list:
            imageName=img['url']
            if imageName.find(".")==-1:
                imageName=imageName+".jpg"
            imageurl = CDN_URL.format(imageName)
            tag = img['tags']
            if (tag):
                tag = ",".join(tag)
            doDownLoad(imageurl, imageName, tag)
            time.sleep(10)


connection = None
TARGET_FOLDER = None
if __name__ == '__main__':
    getTotalSize()
    initDb()
    connection = sqlite3.connect("girlimg.db")
    TARGET_FOLDER = os.path.join(os.getcwd(), "girlimg")
    if (not os.path.exists(TARGET_FOLDER)):
        os.mkdir(TARGET_FOLDER)
    if (TOTAL_COUNT > 0):
        # 容易挂 用单线程
        page = int(TOTAL_COUNT / PAGE_SIZE)
        for i in range(0, page + 1):
            doParseWork(i)
            pass
