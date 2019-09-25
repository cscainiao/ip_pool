import json
import time
import setting
import requests
import redis
import random
from threading import Thread
from multiprocessing import Process

import logging

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s',
                    level=logging.INFO, filename='baidu_log.txt')


class IpTest:

    IP_REDIS_KEY_VALID = setting.VALID_BAIDU_IP_REDIS_KEY
    IP_REDIS_KEY_NOT_VALID = setting.NOT_VALID_IP_REDIS_KEY
    redis_obj = redis.Redis(password=setting.REDIS_PWD)
    special_deal = None

    headers = {
        # 'Referer': 'https://www.douban.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3',
    }

    def __init__(self, t_valid, t_notvalid, test_url, headers=None, max_num=500):
        self.t_valid = t_valid
        self.t_notvalid = t_notvalid
        self.test_url = test_url
        if headers is not None:
            self.headers = headers
        self.max_num = max_num

    def add_special_deal(self, special_deal: str):
        self.special_deal = special_deal

    def test_ip(self, ip_info, is_test_valid):

        ip, score = ip_info['ip'], ip_info['score']
        proxies = {'https': ip, 'http': ip}

        try:
            res = requests.get(self.test_url, headers=self.headers, timeout=5, proxies=proxies, verify=True)
            if res.status_code == 200:
                if not self.special_deal:
                    if not is_test_valid:
                        logging.info('%s: %s可用，添加到可用库' % (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), ip))
                    ip_info['score'] = 10
                    self.redis_obj.rpush(self.IP_REDIS_KEY_VALID, json.dumps(ip_info))
                else:
                    if self.special_deal not in res.text:
                        if not is_test_valid:
                            logging.info('%s: %s可用，添加到可用库' % (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), ip))
                        ip_info['score'] = 10
                        self.redis_obj.rpush(self.IP_REDIS_KEY_VALID, json.dumps(ip_info))
                    else:
                        if is_test_valid:
                            logging.info('%s: %s不可用，添加到不可用库' % (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), ip))
                        ip_info['score'] -= 1
                        if ip_info['score']:
                            self.redis_obj.rpush(self.IP_REDIS_KEY_NOT_VALID, json.dumps(ip_info))
            else:
                if is_test_valid:
                    logging.info('%s: %s不可用，添加到不可用库' % (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), ip))
                ip_info['score'] -= 1
                if ip_info['score']:
                    self.redis_obj.rpush(self.IP_REDIS_KEY_NOT_VALID, json.dumps(ip_info))
        except Exception as e:
            if is_test_valid:
                logging.info('%s: %s不可用，添加到不可用库' % (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), ip))
            ip_info['score'] -= 1
            if ip_info['score']:
                self.redis_obj.rpush(self.IP_REDIS_KEY_NOT_VALID, json.dumps(ip_info))

    def test_valid(self):
        while True:
            try:
                if self.redis_obj.llen(self.IP_REDIS_KEY_VALID) >= self.t_valid:
                    t_list = []
                    for i in range(0, self.t_valid):
                        ip_info = json.loads(self.redis_obj.lpop(self.IP_REDIS_KEY_VALID))
                        if not ip_info:
                            continue
                        t = Thread(target=self.test_ip, args=(ip_info, True))
                        t.start()
                        t_list.append(t)
                    for t in t_list:
                        t.join()
                else:
                    time.sleep(120)
            except Exception as e:
                print(e)
                time.sleep(60)
                continue

    def test_not_valid(self):
        add = False
        while True:
            try:
                len_valid = self.redis_obj.llen(self.IP_REDIS_KEY_VALID)
                if len_valid < self.max_num:
                    add = True
                if add:
                    for _ in range(0, 40):
                        t_list = []
                        for i in range(0, self.t_notvalid):
                            ip_info = json.loads(self.redis_obj.lpop(self.IP_REDIS_KEY_NOT_VALID))
                            if not ip_info:
                                continue
                            t = Thread(target=self.test_ip,
                                       args=(ip_info, False))
                            t.start()
                            t_list.append(t)
                        for t in t_list:
                            t.join()
                    add = False
                time.sleep(300)
            except Exception as e:
                print(e)
                time.sleep(60)
                continue

    def run(self):
        if self.t_valid > 0 and self.t_notvalid > 0:
            p1 = Process(target=self.test_valid)
            p2 = Process(target=self.test_not_valid)
            p1.start()
            p2.start()
            p1.join()
            p2.join()
        if self.t_notvalid > 0:
            self.test_not_valid()
        if self.t_valid > 0:
            self.test_valid()


if __name__ == '__main__':
    test_url = 'https://www.baidu.com/'
    ip_test_obj = IpTest(t_valid=20, t_notvalid=20, test_url=test_url, max_num=2000)
    # ip_test_obj.add_special_deal('登录豆瓣')
    logging.info('-------------------------start--------------------------')
    ip_test_obj.run()
