# -*- coding: utf-8 -*-
import scrapy, os, html
from First.items import FirstItem
from configparser import ConfigParser
import time, requests,re,json
from lxml import etree


class Shuini3Spider(scrapy.Spider):
    name = 'guojiaji_1'
    start_urls = [
        'http://www.jilin.net.cn/gjdt/index.html'
    ]

    def __init__(self):
        self.turn_page = True
        self.logger.info('guojiaji_1.py的日志')
        self.config = ConfigParser()
        self.config.read(os.getcwd() + './spiders/config/config.ini')
        self.items = FirstItem()
        self.items['spider_name'] = 'guojiaji_1'
        try:
            with open(os.getcwd() + '/spiders/url_deduplication/{}.txt'.format('guojiaji_1'), 'r') as f:
                self.url_list = f.read().splitlines()
        except Exception as e:
            self.url_list = []

    def parse(self, response):
        self.items['list_url'] = response.url
        if response.status == 200:
            self.logger.info('采集的列表页URL %s', response.url)
            odd_list = response.xpath('//div[@class="zhx_newslist"]/ul/li')
            for node in odd_list:
                try:
                    self.items['task_name'] = '国家级URL-67-吉林省经济信息网A'
                    content_url = 'http://www.jilin.net.cn/gjdt' + node.xpath('./a/@href').extract()[0]
                    content_url = content_url.replace('./','/')
                    self.items['content_url'] = content_url
                    title = ''.join(node.xpath('./a/text()').extract())
                    self.items['title'] = title.strip()
                    current = self.time_now()
                    self.details_page(content_url)
                    if self.task_filter(current, self.items['publish_date']):
                        yield self.items
                    else:
                        self.turn_page = False
                        break
                except Exception as e:
                    self.items['detail_url'] = ''
                    self.items['status'] = '采集失败'
                    self.items['error'] = '列表页解析失败'
                    self.logger.error('列表页内容解析错误 报错信息为： %s' % e)
                    continue

            if self.turn_page:
                next_page_num = int(response.url.split('/')[-1].resplace('.htm','')) + 1
                next_page_url = '/'.join(response.url.split('/')[:-1]) + '/{}.htm'.format(next_page_num)
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

    def details_page(self, content_url):
        header = {
            'User-Agent': self.config.get('header', 'user_agent'),
            'Accept': self.config.get('header', 'accept'),
            'Accept-Language': self.config.get('header', 'accept_language')
        }
        response = requests.get(content_url, headers=header)
        self.items['detail_url'] = response.url
        if response.status_code == 200:
            res = etree.HTML(response.content)
            try:
                publish_date = res.xpath('//ul[@class="zly_time"]/li/text()')[0].replace('发布日期：','').replace('年','-').replace('月','-').replace('日','').strip()
                self.items['publish_date'] = publish_date
                content_html = res.xpath('//div[@class="TRS_Editor"]')
                html_content = etree.tostring(content_html[0]).decode('utf-8')
                self.items['html_content'] = html.unescape(html_content)
                self.items['pure_content'] = ''.join(re.findall('[\u4e00-\u9fa5]*',self.items['html_content']))
                self.items['origin_source'] = res.xpath('//ul[@class="zly_time"]/li[3]/text()')[0].replace('来源：','')
                self.items['origin_author'] = res.xpath('//ul[@class="zly_time"]/li[2]/text()')[0].replace('作者：','')
                self.items['update_date'] = int(time.time())
                self.items['title_in_content'] = ''
                self.items['status'] = '采集成功'
                self.items['error'] = ''
                self.logger.info('采集的items数据：%s' % self.items)
            except Exception as e:
                self.items['status'] = '采集失败'
                self.items['error'] = '详情页解析失败'
                self.logger.error('详情页解析错误，详情页URL：%s' % content_url)
                self.logger.error('错误详情：%s' % e)
        else:
            self.items['status'] = '采集失败'
            self.items['error'] = '详情页采集失败'


