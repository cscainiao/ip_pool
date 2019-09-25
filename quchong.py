import time

import redis

import setting

def run():
    redis_obj = redis.Redis(password=setting.REDIS_PWD)
    data_not_valid = set(redis_obj.lrange(setting.NOT_VALID_IP_REDIS_KEY,1,10000000))
    data_valid_baidu = set(redis_obj.lrange(setting.VALID_BAIDU_IP_REDIS_KEY,1,10000000))

    redis_obj.delete(setting.NOT_VALID_IP_REDIS_KEY)
    for each_ip in data_not_valid:
        redis_obj.rpush(setting.NOT_VALID_IP_REDIS_KEY,each_ip)

    redis_obj.delete(setting.VALID_BAIDU_IP_REDIS_KEY)
    for each_ip in data_valid_baidu:
        redis_obj.rpush(setting.VALID_BAIDU_IP_REDIS_KEY,each_ip)

    redis_obj.connection_pool.disconnect()


if __name__ == '__main__':
    while True:
        try:
            run()
        except:
            time.sleep(60*60)

        time.sleep(60*60*24)