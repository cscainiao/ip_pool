import asyncio
import json
import os

import aiohttp
import redis
import time
import setting

import logging

log_file_name = os.path.join(setting.log_dir, 'testIpBaidu.log')

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s',
                    level=logging.INFO, filename=log_file_name)
redis_obj = redis.Redis(password=setting.REDIS_PWD)


class IpTest(object):
    IP_REDIS_KEY_VALID = setting.VALID_BAIDU_IP_REDIS_KEY
    IP_REDIS_KEY_NOT_VALID = setting.NOT_VALID_IP_REDIS_KEY
    redis_obj = redis.Redis(password=setting.REDIS_PWD)
    test_url = 'https://www.baidu.com/'

    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    }

    def __init__(self, t_num):
        self.t_num = t_num

    async def test_ip(self, ip_info, semaphore):
        ip, score = ip_info['ip'], ip_info['score']
        real_proxy = 'http://' + ip
        async with semaphore:
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(self.test_url, verify_ssl=True, headers=self.headers, proxy=real_proxy, timeout=10) as response:
                        if response.status:
                            ip_info['score'] = 10
                            redis_obj.rpush(self.IP_REDIS_KEY_VALID, json.dumps(ip_info))
                except Exception as e:
                    logging.info('%s: %s不可用，添加到不可用库' % (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), ip))
                    ip_info['score'] -= 1
                    if ip_info['score']:
                        redis_obj.rpush(self.IP_REDIS_KEY_NOT_VALID, json.dumps(ip_info))

    def run(self):

        while True:
            ip_list = list()
            for _ in range(self.t_num):
                ip_info = self.redis_obj.lpop(self.IP_REDIS_KEY_VALID)
                if ip_info:
                    ip_info = json.loads(ip_info)
                    ip_list.append(ip_info)
            if ip_list:
                semaphore = asyncio.Semaphore(450)
                loop = asyncio.get_event_loop()
                tasks = asyncio.wait([self.test_ip(ip, semaphore) for ip in ip_list])
                loop.run_until_complete(tasks)
            else:
                time.sleep(60)


if __name__ == '__main__':
    ip_test = IpTest(t_num=15)
    ip_test.run()