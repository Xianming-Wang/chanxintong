# -*- coding: utf-8 -*-
import scrapy, os
from First.items import FirstItem
from configparser import ConfigParser
import time, requests
from lxml import etree
import json


class Shuini3Spider(scrapy.Spider):
    name = 'shuini_3'
    # allowed_domains = ['http://www.zybtp.com']
    # API接口直接拿数据
    start_urls = ['http://ec.4008874005.com/webportal/index/bidnotice/getBidNoticeList.do?kind=2&type=&pn=1&search=']

    def __init__(self):
        self.turn_page = True
        self.logger.info('shuini_3.py的日志')
        self.config = ConfigParser()
        self.config.read(os.getcwd() + './spiders/config/config.ini')
        self.items = FirstItem()
        self.items['spider_name'] = 'shuini_3'
        try:
            with open(os.getcwd() + '/spiders/url_deduplication/{}.txt'.format('shuini_3'), 'r') as f:
                self.url_list = f.read().splitlines()
        except Exception as e:
            self.url_list = []

    def parse(self, response):
        self.items['list_url'] = response.url
        if response.status == 200:
            self.logger.info('采集的列表页URL %s', response.url)
            node_list = json.loads(response.text)[0].get('notices')
            for node in node_list:
                try:
                    self.items['task_name'] = '水泥A-4-宁夏建材采购管理平台'
                    id = node.get('id')
                    content_url = 'http://ec.4008874005.com/webportal/index/bidnotice/show/{}.do'.format(id)
                    self.items['content_url'] = content_url
                    title = node.get('purBidProjName')
                    self.items['title'] = title.strip()
                    publish_date = node.get('actPublishDate')
                    self.items['publish_date'] = publish_date

                    current = self.time_now()
                    if self.task_filter(current, publish_date):

                        self.items['html_content'] = node.get('noticeContent')
                        html = etree.HTML(self.items['html_content'])
                        pure_content = ''.join(html.xpath('//p/span/text()')).replace('\xa0', '')
                        self.items['pure_content'] = pure_content

                        self.items['origin_source'] = ''
                        self.items['origin_author'] = ''
                        self.items['update_date'] = int(time.time())
                        self.items['title_in_content'] = ''
                        yield self.items
                    else:
                        self.turn_page = False
                        continue
                except Exception as e:
                    self.items['detail_url'] = ''
                    self.items['status'] = '采集失败'
                    self.items['error'] = '列表页解析失败'
                    self.logger.error('列表页内容解析错误 报错信息为： %s' % e)
                    continue

            if self.turn_page:
                next_page_num = int(str(response.url).split('&')[-2].replace('pn=', '')) + 1
                next_page_url = 'http://ec.4008874005.com/webportal/index/bidnotice/getBidNoticeList.do?kind=2' \
                                '&type=&pn={}&search='.format(next_page_num)
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
