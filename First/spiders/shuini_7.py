# -*- coding: utf-8 -*-
import scrapy, os, html
from First.items import FirstItem
from configparser import ConfigParser
import time, requests
from lxml import etree
import json


class Shuini3Spider(scrapy.Spider):
    name = 'shuini_7'
    # allowed_domains = ['http://www.zybtp.com']
    start_urls = [
        'https://b2b.crcement.com/ispweb/psrmPonNotice/getNoticePage.do?sourceType=&StatusCode='
        '&title=&Orgname=&type=公开&tempcode=1%2C2&rows=0&take=100&skip=0&page=1&pageSize=100'
    ]

    def __init__(self):
        self.turn_page = True
        self.logger.info('shuini_7.py的日志')
        self.config = ConfigParser()
        self.config.read(os.getcwd() + './spiders/config/config.ini')
        self.items = FirstItem()
        self.items['spider_name'] = 'shuini_7'
        try:
            with open(os.getcwd() + '/spiders/url_deduplication/{}.txt'.format('shuini_7'), 'r') as f:
                self.url_list = f.read().splitlines()
        except Exception as e:
            self.url_list = []

    def parse(self, response):
        self.items['list_url'] = response.url
        if response.status == 200:
            self.logger.info('采集的列表页URL https://b2b.crcement.com/ispweb/page/notice/notice_list_wz.jsp')
            odd_list = json.loads(response.text).get("data")
            for node in odd_list:
                try:
                    self.items['task_name'] = '水泥A-8-华润水泥'
                    content_url = 'https://b2b.crcement.com/ispweb/page/notice/notice_info.jsp?type=gb&id={}'.format(node.get('id'))
                    self.items['content_url'] = content_url
                    title = node.get("title")
                    self.items['title'] = title.strip()
                    publish_date = node.get("startDate")
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
                next_page_num = int(str(response.url).split('&')[-2].replace('page=', '')) + 1
                next_page_url = 'https://b2b.crcement.com/ispweb/psrmPonNotice/getNoticePage.do?sourceType=&StatusCode=' \
                                '&title=&Orgname=&type=公开&tempcode=1%2C2&rows=0&take=100&skip=0&page={}&pageSize=100'.format(next_page_num)
                yield scrapy.Request(next_page_url, callback=self.parse)
        else:
            self.items['detail_url'] = ''
            self.items['status'] = '采集失败'
            self.items['error'] = '列表页采集失败'

    def time_now(self):
        current = time.localtime(time.time())
        return current

    def task_filter(self, current, publish_date):
        p_date = time.strptime(publish_date, '%Y-%m-%d %H:%M:%S')
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
                content_html = re.xpath('//div[@class="cont"]')
                html_content = etree.tostring(content_html[0]).decode('utf-8')
                self.items['html_content'] = html.unescape(html_content)
                self.items['pure_content'] = ''.join(re.xpath('//div[@id="infoContent"]/div/p/span/text()')).replace('\xa0', '')
                self.items['origin_source'] = ''
                self.items['origin_author'] = ''
                self.items['update_date'] = int(time.time())
                self.items['title_in_content'] = ''
                self.items['status'] = '采集成功'
                self.items['error'] = ''
                self.logger.info('采集的items数据：%s' % self.items)
                return True
            except Exception as e:
                self.items['status'] = '采集失败'
                self.items['error'] = '详情页解析失败'
                self.logger.error('详情页解析错误，详情页URL：%s' % url)
                self.logger.error('错误详情：%s' % e)
                return False
        else:
            self.items['status'] = '采集失败'
            self.items['error'] = '详情页采集失败'
            return False


