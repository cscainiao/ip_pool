# -*- coding: utf-8 -*-
import time

import redis
import setting
import json


while True:
    r_loc = redis.Redis(password=setting.REDIS_PWD)
    r_2861 = redis.Redis(host='120.77.174.5', password='zk1234567890')

    data1 = r_2861.lrange('weibo_valid_proxies',1,10000000)
    data2 = r_2861.lrange('weibo_proxies_queue',1,10000000)
    ip_all = set()
    for each_data in data1:
        ip_s = str(each_data, 'utf-8')
        if ip_s not in ip_all:
            r_loc.rpush(setting.NOT_VALID_IP_REDIS_KEY, json.dumps({'ip': ip_s, 'score': 100}))
            ip_all.add(ip_s)

    for each_data in data2:
        ip_s = str(each_data, 'utf-8')
        if ip_s not in ip_all:
            r_loc.rpush(setting.NOT_VALID_IP_REDIS_KEY, json.dumps({'ip': ip_s, 'score': 100}))
            ip_all.add(ip_s)
    r_loc.connection_pool.disconnect()
    r_2861.connection_pool.disconnect()
    print('ok')
    time.sleep(60*60*24*7)
