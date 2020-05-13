# -*- coding: utf-8 -*-
import scrapy, os, html
from First.items import FirstItem
import time, requests, re
from lxml import etree
from configparser import ConfigParser


class ShuiniSpider(scrapy.Spider):
    name = 'gonglu'
    start_urls = [
        'https://news.lmjx.net/n_product.html?p=1',
        'https://news.lmjx.net/n_industry.html?p=1'
    ]

    def __init__(self):
        self.logger.info('gonglu.py的日志')
        self.turn_page = True
        self.config = ConfigParser()
        self.config.read(os.getcwd() + './spiders/config/config.ini')
        self.items = FirstItem()
        self.items['spider_name'] = 'gonglu'
        try:
            with open(os.getcwd() + '/spiders/url_deduplication/{}.txt'.format('gonglu'), 'r') as f:
                self.url_list = f.read().splitlines()
        except Exception as e:
            self.url_list = []

    def parse(self, response):
        self.items['list_url'] = response.url
        if response.status == 200:
            self.logger.info('采集的列表页URL %s', response.url)
            node_list = response.xpath('//div[@id="i_clist_1"]/div[@class="item"]')
            for node in node_list:
                try:
                    if response.url.find('n_product') != -1:
                        self.items['task_name'] = '公路桥梁A-20-中国路面机械网'
                    else:
                        self.items['task_name'] = '公路桥梁A-19-中国路面机械网'
                    content_url = node.xpath('./h1/a/@href').extract()[0]
                    self.items['content_url'] = content_url
                    self.items['title'] = node.xpath('./h1/a/text()').extract()[0]
                    publish_date = node.xpath('./div[@class="ptxt"]/label/text()').extract()[-1].strip()
                    self.items['publish_date'] = publish_date
                except Exception as e:
                    self.items['detail_url'] = ''
                    self.items['status'] = '采集失败'
                    self.items['error'] = '列表页解析失败'
                    self.logger.error('列表页内容解析错误 报错信息为： %s' %e )
                    continue
                current = self.time_now()
                if self.task_filter(current, publish_date):
                    self.details_page(content_url)
                    yield self.items
                else:
                    self.turn_page = False
                    continue
            if self.turn_page:
                next_page_num = int(str(response.url).split('=')[-1]) + 1
                next_page_url = str(response.url).split('=')[0] + str(next_page_num)
                yield scrapy.Request(next_page_url, callback=self.parse)
        else:
            self.items['detail_url'] = ''
            self.items['status'] = '采集失败'
            self.items['error'] = '列表页采集失败'

    def time_now(self):
        current = time.localtime(time.time())
        return current

    def task_filter(self, current, publish_date):
        publish_date = publish_date.split(' ')[0]
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
            res = etree.HTML(response.content)  # 为什么不能用content而是text
            try:
                content_html = res.xpath('//content')
                html_content = etree.tostring(content_html[0]).decode('UTF-8')
                self.items['html_content'] = html.unescape(html_content)
                self.items['pure_content'] = ''.join(re.findall('[\u4e00-\u9fa5]*',self.items['html_content']))
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




