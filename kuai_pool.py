import json
import logging

import redis
import requests
import time
from bs4 import BeautifulSoup
import random

import setting

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s',
                    level=logging.INFO, filename='kuaidaili_log.txt')
IP_REDIS_KEY_NOT_VALID = setting.NOT_VALID_IP_REDIS_KEY
redis_obj = redis.Redis(password=setting.REDIS_PWD)

class KuaiPool(object):
    def __init__(self):
        self.Headers = {
            'Host':'www.kuaidaili.com',
            'Referer':'https://www.kuaidaili.com/',
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36'

        }
        self.start_urls = 'https://www.kuaidaili.com/free/'
        self.verity_url = 'https://www.baidu.com/'
        self.keep_session = requests.session()
        self.verity_headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36'}

    def login(self, url):

        data = {
            'next': '',
            'kf5_return_to': '',
            'username': '18584918401',
            'passwd': 'AS8803461'
        }
        res = self.keep_session.post(url=url,headers=self.Headers,data=data,timeout=5)
        if res.status_code == 200:
            logging.info('login ok!')
        else:
            logging.error('login fail ！')
        time.sleep(3)

    def gethtml(self, url):
        try:
            response = self.keep_session.get(url=url,headers=self.Headers,timeout=3)
            response = response.text
            if 'Invalid' in response:
                return 'Invalid'
            ip_list = list()
            soup = BeautifulSoup(response,'lxml')
            trs = soup.find('tbody').find_all('tr')
            for tr in trs:
                tds = tr.find_all('td')
                ip = tds[0].text.strip()
                port = tds[1].text.strip()
                anony = tds[2].text.strip()
                protocol = tds[3].text.strip()
                speed = tds[4].text.strip()
                time = tds[5].text.strip()
                ip_list.append(ip+':'+port)
            logging.info('get ip ok %s' % url)
            return ip_list
        except Exception as e:
            logging.warning('%s get ip error %s' % (url, e))
            return []


if __name__ == '__main__':
    while True:
        kuai_daili = KuaiPool()
        try:
            kuai_daili.login(url='https://www.kuaidaili.com/login/')
        except Exception as e:
            logging.error('login fail %s' % e)
        for n in range(1, 20):
            url = 'https://www.kuaidaili.com/free/inha/'+str(n)
            ret = kuai_daili.gethtml(url=url)
            if ret == 'Invalid':
                logging.info('today get ip gaoni over')
                break
            for each_ip in ret:
                redis_obj.rpush(IP_REDIS_KEY_NOT_VALID, json.dumps({'ip': each_ip, 'score': 10}))
            time.sleep(random.randint(3,5))

        for n in range(1, 20):
            url = 'https://www.kuaidaili.com/free/intr/'+str(n)
            ret = kuai_daili.gethtml(url=url)
            if ret == 'Invalid':
                logging.info('today get ip putong over')
                break
            for each_ip in ret:
                redis_obj.rpush(IP_REDIS_KEY_NOT_VALID, json.dumps({'ip': each_ip, 'score': 10}))
            time.sleep(random.randint(3,5))

        time.sleep(60*60*24)
