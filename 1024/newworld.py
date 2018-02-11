# -*- coding: utf-8 -*-
import requests, os, threading, queue, re
from bs4 import BeautifulSoup

BASE_URL = 'http://pp.wedid.us/'
WORLD_URL = 'thread0806.php?fid=8'
queue = queue.Queue()
THREAD_NUM=10

#获取最新官方地址，todo
def getMainUrl():
    pass


def getRequestContent(url, stream=False):
    try:
        response = requests.get(url, stream)
        if (response.status_code == 200):
            return response
        return None
    except Exception as e:
        print("访问{0}失败={1}", url, e)
    pass


class Content(object):
    def __init__(self, url, title, type):
        self.url = url
        self.type = type
        self.title = title.strip()


class Worker(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        try:
            while (True):
                content = queue.get(timeout=10)
                self.work(content)
        except:
            print("读取队列信息失败")
            pass

    def work(self, content):
        if content:
            bbsurl = BASE_URL+content.url
            print("开始获取帖子总回复数{0}".format(bbsurl))
            response = getRequestContent(bbsurl)
            if (response):
                try:
                    bs = BeautifulSoup(response.content, 'lxml')
                    path=BASE_PATH
                    if(content.type):
                        path = os.path.join(path,content.type)
                        if not os.path.isdir(path):
                            os.mkdir(path)
                    path = os.path.join(path, content.title)
                    if not os.path.isdir(path):
                        os.mkdir(path)
                    div=bs.select_one('div.tpc_content.do_not_catch').find_all('input')
                    if(div):
                        for input in div:
                            imgurl=input['src']
                            self.downImg(imgurl, os.path.join(path, imgurl.split('/')[-1]))
                except Exception as e:
                    print("抓取失败{0},reason={1}".format(content.url, e))

    def downImg(self, url, target_file):
        print("开始下载文件,地址为{0}".format(url))
        if os.path.isfile(target_file):
            print("文件已存在,本次不下载")
            return
        response = getRequestContent(url)
        if response:
            with open(target_file, 'wb') as f:
                f.write(response.content)

def parsePage():
    url = BASE_URL + WORLD_URL
    response = getRequestContent(url)
    if response:
        bs = BeautifulSoup(response.content, 'lxml')
        pageNum = getPage(bs)
        print("MAIN=》开始解析帖子列表当前板块id={0},总页数{1}".format(url, pageNum))
        if (pageNum > 2):
            for i in range(2, pageNum+1):
                addUrlToQueue(url + '&page=' + str(i))
    pass


r = re.compile('^(\[.*?])(.*)$')


def addUrlToQueue(url):
    response = getRequestContent(url)
    if (response):
        bs = BeautifulSoup(response.content, 'lxml')
        tr = bs.find(id="ajaxtable").find_all('tr', class_='tr2')[-1].find_next_siblings('tr', class_='tr3')
        for t in tr:
            td = t.find(class_='tal')
            type=None
            title = td.text.strip().replace('\r','').replace('\n','').replace('\t','')
            match=re.match(r,title)
            if match:
                type=match.group(1)
                title=match.group(2)
            url = td.find('a')['href']
            print("增加url到队列{0}".format(url))
            queue.put(Content(url, title,type))


def getPage(bs):
    pageNum = 1
    try:
        pageNum = int(bs.select_one("a.w70").find('input')['value'].split('/')[-1])
    except:
        pass
    return pageNum

BASE_PATH=None
if __name__ == '__main__':
    BASE_PATH = os.path.join(os.getcwd(), '91photo')
    if not os.path.isdir(BASE_PATH):
        os.mkdir(BASE_PATH)
    for i in range(THREAD_NUM):
        Worker().start()
    parsePage()
