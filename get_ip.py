import time
from time import sleep
import setting
import redis
import requests


r_my = redis.Redis(password=setting.REDIS_PWD)
redis_key = 'caipanwenshu_queue'


def get_ips():
    try:
        req_ret = requests.get(
            'http://vtp.daxiangdaili.com/ip/?tid=557447370288726'
            '&num=50&delay=2&format=json&filter=on'
        )
        # meb
        # url = 'http://api.wandoudl.com/api/ip?app_key=7aaabcc48e4bbf7586848b9b417bec96&pack=2&num=1&xy=1&type=2&lb=\r\n&mr=1'
        if req_ret.status_code == 200:
            json_data = req_ret.json()
            for each_data in json_data:
                # get_ip_list.append({'ip': each_data['host'], 'port': each_data['port']})
                key = str(each_data['host']) + ':' + str(each_data['port'])
                r_my.rpush(redis_key, key)
        time_now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        print('%s : sync ok' % time_now)
    except:
        pass


while True:
    len_valid = r_my.llen(redis_key)
    if len_valid < 20:
        get_ips()
    sleep(10)
