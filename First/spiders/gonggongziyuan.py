# -*- coding: utf-8 -*-
import scrapy, os, html
from First.items import FirstItem
from configparser import ConfigParser
import time, requests, json
from lxml import etree


class Shuini3Spider(scrapy.Spider):
    name = 'gonggongziyuan'
    start_urls = [
        'http://hnsggzyfwpt.hndrc.gov.cn/services/hl/getSelect?response=application/json&pageIndex=1&pageSize=100'
        '&day=&sheng=x1&qu=&xian=&title=&timestart=&timeend=&categorynum=002001001'
        '&siteguid=9f5b36de-4e8f-4fd6-b3a1-a8e08b38ea38'
    ]

    def __init__(self):
        self.turn_page = True
        self.logger.info('gonggongziyuan.py的日志')
        self.config = ConfigParser()
        self.config.read(os.getcwd() + './spiders/config/config.ini')
        self.items = FirstItem()
        self.items['spider_name'] = 'gonggongziyuan'
        try:
            with open(os.getcwd() + '/spiders/url_deduplication/{}.txt'.format('gonggongziyuan'), 'r') as f:
                self.url_list = f.read().splitlines()
        except Exception as e:
            self.url_list = []

    def parse(self, response):
        self.items['list_url'] = response.url
        if response.status == 200:
            self.logger.info('采集的列表页URL %s', response.url)
            text = response.text
            json_data = json.loads(text)
            odd_list = json_data.get('return')
            nodelist = json.loads(odd_list).get('Table')
            for node in nodelist:
                try:
                    self.items['task_name'] = '公共资源交易A-188-河南省'
                    content_url = 'http://hnsggzyfwpt.hndrc.gov.cn' + node.get('href')
                    self.items['content_url'] = content_url
                    self.items['title'] = node.get('title')
                    publish_date = node.get('infodate')
                    self.items['publish_date'] = publish_date
                except Exception as e:
                    self.items['detail_url'] = ''
                    self.items['status'] = '采集失败'
                    self.items['error'] = '列表页解析失败'
                    self.logger.error('列表页内容解析错误 报错信息为： %s' % e)
                    continue

                current = self.time_now()
                if self.task_filter(current, publish_date):
                    self.details_page(content_url)
                    yield self.items
                else:
                    self.turn_page = False
                    continue
            if self.turn_page:
                next_page_num = int(str(response.url).split('-5-')[-1].replace('.html', '')) + 1
                next_page_url = 'http://www.cncrcc.com/listinfo-5-{}.html'.format(next_page_num)
                yield scrapy.Request(next_page_url, callback=self.parse)
        else:
            self.items['detail_url'] = ''
            self.items['status'] = '采集失败'
            self.items['error'] = '列表页采集失败'

    def time_now(self):
        current = time.localtime(time.time())
        return current

    def task_filter(self, current, publish_date):
        p_date = time.strptime(publish_date, '%Y-%m-%d')
        if current.tm_mon == p_date.tm_mon and current.tm_mday == p_date.tm_mday \
                and self.items['content_url'] not in self.url_list:
            return True
        else:
            return False

    def details_page(self, url):
        header = {
            'User-Agent': self.config.get('header', 'user_agent'),
            'Accept': self.config.get('header', 'accept'),
            'Accept-Language': self.config.get('header', 'accept_language')
        }
        response = requests.get(url, headers=header)
        self.items['detail_url'] = response.url
        if response.status_code == 200:
            re = etree.HTML(response.text)  # 为什么不能用content而是text
            try:
                content_html = re.xpath('//div[@class="ewb-left-bd"]')
                html_content = etree.tostring(content_html[0]).decode('utf-8')
                self.items['html_content'] = html.unescape(html_content)
                self.items['pure_content'] = ''.join(re.xpath('//p/*/text()')).strip()
                self.items['origin_source'] = ''
                self.items['origin_author'] = ''
                self.items['update_date'] = int(time.time())
                self.items['title_in_content'] = ''
                self.items['status'] = '采集成功'
                self.items['error'] = ''
                self.logger.info('采集的items数据：%s' % self.items)
            except Exception as e:
                self.items['status'] = '采集失败'
                self.items['error'] = '详情页解析失败'
                self.logger.error('详情页解析错误，详情页URL：%s' % url)
                self.logger.error('错误详情：%s' % e)
        else:
            self.items['status'] = '采集失败'
            self.items['error'] = '详情页采集失败'


