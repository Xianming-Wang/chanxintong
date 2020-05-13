# -*- coding: utf-8 -*-

import scrapy, os, html
from First.items import FirstItem
from configparser import ConfigParser
import time, requests, re
from lxml import etree


class Shuini3Spider(scrapy.Spider):
    name = 'yiqiyibiao_1'
    start_urls = [
        'http://news.hi1718.com/'
    ]

    def __init__(self):
        self.logger.info('yiqiyibiao_1.py的日志')
        self.config = ConfigParser()
        self.config.read(os.getcwd() + './spiders/config/config.ini')
        self.items = FirstItem()
        self.items['spider_name'] = 'yiqiyibiao_1'
        try:
            with open(os.getcwd() + '/spiders/url_deduplication/{}.txt'.format('yiqiyibiao_1'), 'r') as f:
                self.url_list = f.read().splitlines()
        except Exception as e:
            self.url_list = []

    def parse(self, response):
        self.items['list_url'] = response.url
        if response.status == 200:
            self.logger.info('采集的列表页URL %s', response.url)
            odd_list = response.xpath('//div[@class="info-item mt10"]/div/div')
            for node in odd_list:
                try:
                    self.items['task_name'] = '机械仪器仪表A-46-维库仪器仪表网'
                    content_url = node.xpath('./div[2]/p/a/@href').extract()[0]
                    self.items['content_url'] = content_url
                    title = ''.join(node.xpath('./div[2]/p/a/b/text()').extract())
                    self.items['title'] = title.strip()
                    publish_date = node.xpath('.//div[2]/p[3]/span[2]/text()').extract()[0].replace('时间：', '')
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
                    continue
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

    def details_page(self, content_url):
        header = {
            'User-Agent': self.config.get('header', 'user_agent'),
            'Accept': self.config.get('header', 'accept'),
            'Accept-Language': self.config.get('header', 'accept_language')
        }

        response = requests.get(content_url, headers=header)
        self.items['detail_url'] = response.url
        if response.status_code == 200:
            res = etree.HTML(response.text)  # 为什么不能用content而是text
            try:
                content_html = res.xpath('//div[@class="info-details-content clearfix"]')
                html_content = etree.tostring(content_html[0]).decode('utf-8')
                self.items['html_content'] = html.unescape(html_content)
                self.items['pure_content'] = ''.join(re.findall('[\u4e00-\u9fa5]*',self.items['html_content']))
                tx = res.xpath('//div[@class="info-details-title txt-c"]/p/text()')[0]
                self.items['origin_source'] = tx.split('出处：')[-1].split('发布于：')[0]
                self.items['origin_author'] = ''
                self.items['update_date'] = int(time.time())
                self.items['title_in_content'] = ''
                self.logger.info('采集的items数据：%s' % self.items)
                self.items['status'] = '采集成功'
                self.items['error'] = ''
            except Exception as e:
                self.items['status'] = '采集失败'
                self.items['error'] = '详情页解析失败'
                self.logger.error('详情页解析错误，详情页URL：%s' % content_url)
                self.logger.error('错误详情：%s' % e)
        else:
            self.items['status'] = '采集失败'
            self.items['error'] = '详情页采集失败'


