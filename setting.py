# ip pool setting

IS_DEV = True

if IS_DEV:
    REDIS_PWD = None
else:
    REDIS_PWD = 'xx117501'

NOT_VALID_IP_REDIS_KEY = 'not_valid'

VALID_BAIDU_IP_REDIS_KEY = 'valid_baidu'

