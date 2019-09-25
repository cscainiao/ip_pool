import json

from flask import Flask
import setting
import redis
app = Flask(__name__)


@app.route('/get_ip/<string:redis_key>/<int:num>')
def index(redis_key, num):
    try:
        redis_obj = redis.Redis(password=setting.REDIS_PWD)
        data = dict()
        ip_list = list()
        for _ in range(0, num):
            ip_r = json.loads(redis_obj.rpop(redis_key))
            if ip_r:
                ip_list.append(ip_r['ip'])
            redis_obj.lpush(redis_key, json.dumps(ip_r))
        data['ip_list'] = ip_list
        data['ok'] = 1
        redis_obj.connection_pool.disconnect()
        return data
    except Exception as e:
        return {'ip_list':[], 'ok':0, 'msg': e}


if __name__ == "__main__":
    app.run(debug=False, port=5000, host='0.0.0.0')
