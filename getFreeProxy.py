# -*- coding: utf-8 -*-
import hashlib
import json
import logging
import random
import re
import time

import execjs
import redis
import requests
from lxml import etree
from requests import Response
# for debug to disable insecureWarning
import setting

requests.packages.urllib3.disable_warnings()

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s',
                    level=logging.INFO)
IP_REDIS_KEY_NOT_VALID = setting.NOT_VALID_IP_REDIS_KEY


def getHtmlTree(url, **kwargs):
    """
    获取html树
    :param url:
    :param kwargs:
    :return:
    """

    header = {'Connection': 'keep-alive',
              'Cache-Control': 'max-age=0',
              'Upgrade-Insecure-Requests': '1',
              'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko)',
              'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
              'Accept-Encoding': 'gzip, deflate, sdch',
              'Accept-Language': 'zh-CN,zh;q=0.8',
              }
    # TODO 取代理服务器用代理服务器访问
    wr = WebRequest()
    html = wr.get(url=url, header=header).content
    return etree.HTML(html)


class WebRequest(object):
    def __init__(self, *args, **kwargs):
        pass

    @property
    def user_agent(self):
        """
        return an User-Agent at random
        :return:
        """
        ua_list = [
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71',
            'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)',
            'Mozilla/5.0 (Windows NT 5.1; U; en; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.50',
            'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0',
        ]
        return random.choice(ua_list)

    @property
    def header(self):
        """
        basic header
        :return:
        """
        return {'User-Agent': self.user_agent,
                'Accept': '*/*',
                'Connection': 'keep-alive',
                'Accept-Language': 'zh-CN,zh;q=0.8'}

    def get(self, url, header=None, retry_time=5, timeout=30,
            retry_flag=list(), retry_interval=5, *args, **kwargs):
        """
        get method
        :param url: target url
        :param header: headers
        :param retry_time: retry time when network error
        :param timeout: network timeout
        :param retry_flag: if retry_flag in content. do retry
        :param retry_interval: retry interval(second)
        :param args:
        :param kwargs:
        :return:
        """
        headers = self.header
        if header and isinstance(header, dict):
            headers.update(header)
        while True:
            try:
                html = requests.get(url, headers=headers, timeout=timeout, **kwargs)
                if any(f in html.content for f in retry_flag):
                    raise Exception
                return html
            except Exception as e:
                print(e)
                retry_time -= 1
                if retry_time <= 0:
                    # 多次请求失败
                    resp = Response()
                    resp.status_code = 200
                    return resp
                time.sleep(retry_interval)


class GetFreeProxy(object):
    """
    proxy getter
    """

    @staticmethod
    def freeProxy01():
        """
        无忧代理 http://www.data5u.com/
        几乎没有能用的
        :return:
        """
        url_list = [
            'http://www.data5u.com/',
            'http://www.data5u.com/free/gngn/index.shtml',
            'http://www.data5u.com/free/gnpt/index.shtml'
        ]
        key = 'ABCDEFGHIZ'
        for url in url_list:
            html_tree = getHtmlTree(url)
            ul_list = html_tree.xpath('//ul[@class="l2"]')
            for ul in ul_list:
                try:
                    ip = ul.xpath('./span[1]/li/text()')[0]
                    classnames = ul.xpath('./span[2]/li/attribute::class')[0]
                    classname = classnames.split(' ')[1]
                    port_sum = 0
                    for c in classname:
                        port_sum *= 10
                        port_sum += key.index(c)
                    port = port_sum >> 3
                    yield '{}:{}'.format(ip, port)
                except Exception as e:
                    print(e)

    @staticmethod
    def freeProxy02(count=300):
        """
        代理66 http://www.66ip.cn/
        :param count: 提取数量
        :return:
        """
        urls = [
            'http://www.66ip.cn/mo.php?sxb=&tqsl={}&port=&export=&ktip=&sxa=&submit=%CC%E1++%C8%A1&textarea='.format(count),
            'http://www.66ip.cn/nmtq.php?getnum={}&isp=0&anonymoustype=0&start=&ports=&export=&ipaddress=&area=0&proxytype=2&api=66ip'.format(count)
        ]

        for url in urls:
            try:
                html = requests.get(url).text
                ips = re.findall(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}", html)
                for ip in ips:
                    yield ip.strip()
            except Exception as e:
                print(e)
                pass

    @staticmethod
    def freeProxy03(page_count=5):
        """
        西刺代理 http://www.xicidaili.com
        :return:
        """
        url_list = [
            'http://www.xicidaili.com/nn/',  # 高匿
            'http://www.xicidaili.com/nt/',  # 透明
        ]
        for each_url in url_list:
            for i in range(1, page_count + 1):
                page_url = each_url + str(i)
                tree = getHtmlTree(page_url)
                proxy_list = tree.xpath('.//table[@id="ip_list"]//tr[position()>1]')
                for proxy in proxy_list:
                    try:
                        yield ':'.join(proxy.xpath('./td/text()')[0:2])
                    except Exception as e:
                        pass

    @staticmethod
    def freeProxy04():
        """
        guobanjia http://www.goubanjia.com/
        :return:
        """
        url = "http://www.goubanjia.com/"
        tree = getHtmlTree(url)
        proxy_list = tree.xpath('//td[@class="ip"]')
        # 此网站有隐藏的数字干扰，或抓取到多余的数字或.符号
        # 需要过滤掉<p style="display:none;">的内容
        xpath_str = """.//*[not(contains(@style, 'display: none'))
                                        and not(contains(@style, 'display:none'))
                                        and not(contains(@class, 'port'))
                                        ]/text()
                                """
        for each_proxy in proxy_list:
            try:
                # :符号裸放在td下，其他放在div span p中，先分割找出ip，再找port
                ip_addr = ''.join(each_proxy.xpath(xpath_str))

                # HTML中的port是随机数，真正的端口编码在class后面的字母中。
                # 比如这个：
                # <span class="port CFACE">9054</span>
                # CFACE解码后对应的是3128。
                port = 0
                for _ in each_proxy.xpath(".//span[contains(@class, 'port')]"
                                          "/attribute::class")[0]. \
                        replace("port ", ""):
                    port *= 10
                    port += (ord(_) - ord('A'))
                port /= 8

                yield '{}:{}'.format(ip_addr, int(port))
            except Exception as e:
                pass

    @staticmethod
    def freeProxy05(page=10):
        """
        快代理 https://www.kuaidaili.com
        """
        url_list = [
            'https://www.kuaidaili.com/free/inha/%s/',
            'https://www.kuaidaili.com/free/intr/%s/'
        ]
        for url in url_list:
            for p in range(1, page):
                tree = getHtmlTree(url % p)
                proxy_list = tree.xpath('.//table//tr')
                time.sleep(1)  # 必须sleep 不然第二条请求不到数据
                for tr in proxy_list[1:]:
                    yield ':'.join(tr.xpath('./td/text()')[0:2])

    @staticmethod
    def freeProxy06():
        """
        码农代理 https://proxy.coderbusy.com/
        已经不能打开网页了
        """
        urls = ['https://proxy.coderbusy.com/']
        for url in urls:
            tree = getHtmlTree(url)
            proxy_list = tree.xpath('.//table//tr')
            for tr in proxy_list[1:]:
                yield ':'.join(tr.xpath('./td/text()')[0:2])

    @staticmethod
    def freeProxy07(page=10):
        """
        云代理 http://www.ip3366.net/free/
        :return:
        """
        urls = ['http://www.ip3366.net/free/?stype=1&page=%s',
                "http://www.ip3366.net/free/?stype=2&page=%s"]
        request = WebRequest()
        for url in urls:
            for p in range(1, page):
                time.sleep(1)
                r = request.get(url % p, timeout=10)
                proxies = re.findall(r'<td>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td>[\s\S]*?<td>(\d+)</td>', r.text)
                for proxy in proxies:
                    yield ":".join(proxy)

    @staticmethod
    def freeProxy08():
        """
        IP海 http://www.iphai.com/free/ng
        网页打不开了
        """
        urls = [
            'http://www.iphai.com/free/ng',
            'http://www.iphai.com/free/np',
            'http://www.iphai.com/free/wg',
            'http://www.iphai.com/free/wp'
        ]
        request = WebRequest()
        for url in urls:
            r = request.get(url, timeout=10)
            proxies = re.findall(r'<td>\s*?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s*?</td>[\s\S]*?<td>\s*?(\d+)\s*?</td>',
                                 r.text)
            for proxy in proxies:
                yield ":".join(proxy)

    @staticmethod
    def freeProxy09(page_count=10):
        """
        https://www.freeip.top/?page=
        全球代理：有许多国外的代理
        :return:
        """
        for i in range(1, page_count + 1):
            url = 'https://www.freeip.top/?page={}'.format(i)
            html_tree = getHtmlTree(url)
            tr_list = html_tree.xpath(".//tbody//tr")
            if len(tr_list) == 0:
                continue
            for tr in tr_list:
                yield tr.xpath("./td[1]/text()")[0] + ":" + tr.xpath("./td[2]/text()")[0]

    @staticmethod
    def freeProxy13(max_page=10):
        """
        http://www.qydaili.com/free/?action=china&page=1
        齐云代理
        :param max_page:
        :return:
        """
        base_url = 'http://www.qydaili.com/free/?action=china&page='
        request = WebRequest()
        for page in range(1, max_page + 1):
            url = base_url + str(page)
            r = request.get(url, timeout=10)
            proxies = re.findall(
                r'<td.*?>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td>[\s\S]*?<td.*?>(\d+)</td>',
                r.text)
            for proxy in proxies:
                yield ':'.join(proxy)

    @staticmethod
    def freeProxy14(max_page=10):
        """
        http://www.89ip.cn/index.html
        89免费代理
        :param max_page:
        :return:
        """
        base_url = 'http://www.89ip.cn/index_{}.html'
        request = WebRequest()
        for page in range(1, max_page + 1):
            url = base_url.format(page)
            r = request.get(url, timeout=10)
            proxies = re.findall(
                r'<td.*?>[\s\S]*?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})[\s\S]*?</td>[\s\S]*?<td.*?>[\s\S]*?(\d+)[\s\S]*?</td>',
                r.text)
            for proxy in proxies:
                yield ':'.join(proxy)

    @staticmethod
    def freeProxy15():
        """
        零度代理, 不能使用
        """
        def get_token(page, timestamp):
            token = str(page) + '15' + str(timestamp)
            hl = hashlib.md5()
            hl.update(token.encode(encoding='utf-8'))
            return hl.hexdigest()

        node = execjs.get()
        ctx = node.compile(open('js/nyloner.js').read())
        session = requests.session()
        session.get('https://nyloner.cn/proxy', headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'
        })
        for page in range(1, 11):
            try:
                timestamp = int(time.time())
                token = get_token(page, timestamp)
                url = 'https://nyloner.cn/proxy?page=%s&num=15&token=%s&t=%s' % (page, token, timestamp)

                resp = session.get(url, timeout=5)
                list_str = resp.json()['list']
                list_str = ctx.call("decode_str", list_str)
                data_json = json.loads(list_str)
                for ip_info in data_json:
                    yield ip_info['ip'] + ':' + ip_info['port']
            except:
                time.sleep(2)


class CheckProxy(object):

    @staticmethod
    def checkAllGetProxyFunc():
        """
        检查getFreeProxy所有代理获取函数运行情况
        Returns:
            None
        """
        import inspect
        member_list = inspect.getmembers(GetFreeProxy, predicate=inspect.isfunction)
        proxy_count_dict = dict()
        for func_name, func in member_list:
            logging.info(u"开始运行 {}".format(func_name))
            try:
                proxy_list = [_ for _ in func() if verifyProxyFormat(_)]
                proxy_count_dict[func_name] = len(proxy_list)
            except Exception as e:
                logging.error(u"代理获取函数 {} 运行出错!".format(func_name))
                logging.error(str(e))
        logging.info(u"所有函数运行完毕 " + "***" * 5)
        for func_name, func in member_list:
            logging.info(u"函数 {n}, 获取到代理数: {c}".format(n=func_name, c=proxy_count_dict.get(func_name, 0)))

    @staticmethod
    def checkGetProxyFunc(func):
        """
        检查指定的getFreeProxy某个function运行情况
        Args:
            func: getFreeProxy中某个可调用方法

        Returns:
            None
        """
        func_name = getattr(func, '__name__', "None")
        logging.info("==============================start running func: {}============================================".format(func_name))
        count = 0
        for proxy in func():
            if verifyProxyFormat(proxy):
                logging.info("{} fetch proxy: {}".format(func_name, proxy))
                redis_obj.rpush(IP_REDIS_KEY_NOT_VALID, json.dumps({'ip': proxy, 'score': 10}))
                count += 1
        logging.info("----------------------------{n} completed, fetch proxy number: {c}-----------------------------".format(n=func_name, c=count))


def verifyProxyFormat(proxy):
    """
    检查代理格式
    :param proxy:
    :return:
    """
    import re
    verify_regex = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}"
    _proxy = re.findall(verify_regex, proxy)
    return True if len(_proxy) == 1 and _proxy[0] == proxy else False


if __name__ == '__main__':

        redis_obj = redis.Redis(password=setting.REDIS_PWD)
        CheckProxy = CheckProxy()
        while True:
            # try:
            #     CheckProxy.checkGetProxyFunc(GetFreeProxy.freeProxy01)
            # except Exception as e:
            #     logging.error('freeProxy01 error %s '% e)
            # try:
            #     CheckProxy.checkGetProxyFunc(GetFreeProxy.freeProxy02)
            # except Exception as e:
            #     logging.error('freeProxy02 error %s ' % e)
            # try:
            #     CheckProxy.checkGetProxyFunc(GetFreeProxy.freeProxy03)
            # except Exception as e:
            #     logging.error('freeProxy03 error %s '% e)
            # try:
            #     CheckProxy.checkGetProxyFunc(GetFreeProxy.freeProxy04)
            # except Exception as e:
            #     logging.error('freeProxy04 error %s '% e)
            # try:
            #     CheckProxy.checkGetProxyFunc(GetFreeProxy.freeProxy05)
            # except Exception as e:
            #     logging.error('freeProxy05 error %s '% e)
            # try:
            #     CheckProxy.checkGetProxyFunc(GetFreeProxy.freeProxy07)
            # except Exception as e:
            #     logging.error('freeProxy07 error %s ' % e)
            #
            # try:
            #     CheckProxy.checkGetProxyFunc(GetFreeProxy.freeProxy09)
            # except Exception as e:
            #     logging.error('freeProxy09 error %s '% e)
            # try:
            #     CheckProxy.checkGetProxyFunc(GetFreeProxy.freeProxy13)
            # except Exception as e:
            #     logging.error('freeProxy13 error %s '% e)
            # try:
            #     CheckProxy.checkGetProxyFunc(GetFreeProxy.freeProxy14)
            # except Exception as e:
            #     logging.error('freeProxy14 error %s '% e)

            time.sleep(60*60*1)
