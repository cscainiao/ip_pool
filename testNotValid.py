import asyncio
import time
from time import sleep
import aiohttp
import redis
import setting


IP_REDIS_KEY_VALID = 'weibo_proxies_queue'
IP_REDIS_KEY_NOT_VALID = 'weibo_proxies'

# ======================================================================
url = 'http://sccxtp.newssc.org/cxpx/Vaptcha/CodeViable?id=1346'
headers = {
    # 'Referer': 'https://www.bilibili.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3',
}
# ======================================================================

r = redis.Redis(password=setting.REDIS_PWD)


class WeiBo(object):

    async def test_ip(self, ip, semaphore):

        real_proxy = 'http://' + ip
        async with semaphore:
            async with aiohttp.ClientSession() as session:
                try:
                    # sleep(2)
                    async with session.get(url, verify_ssl=True, headers=headers, proxy=real_proxy, timeout=10) as response:
                        if response.status == 200:
                            print('%s: %s可用，添加到可用库' % (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), ip))
                            r.rpush(IP_REDIS_KEY_VALID, ip)

                        else:
                            r.rpush(IP_REDIS_KEY_NOT_VALID, ip)
                except Exception as e:
                    r.rpush(IP_REDIS_KEY_NOT_VALID, ip)

    def run(self, ip_test):
        semaphore = asyncio.Semaphore(450)
        loop = asyncio.get_event_loop()
        tasks = asyncio.wait([self.test_ip(ip, semaphore) for ip in ip_test])
        loop.run_until_complete(tasks)


if __name__ == '__main__':
    add = False
    weibo = WeiBo()
    while True:
        try:
            len_valid = r.llen(IP_REDIS_KEY_VALID)
            if len_valid < 500:
                add = True
            if add:
                for _ in range(0, 40):
                    test_ip_l = []
                    for i in range(0, 15):
                        test_ip_l.append(str(r.lpop(IP_REDIS_KEY_NOT_VALID), 'utf-8'))
                    weibo.run(test_ip_l)
                add = False
            sleep(300)
        except Exception as e:
            print(e)
            sleep(60)
            continue
