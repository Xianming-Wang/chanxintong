# -*- coding: utf-8 -*-
import scrapy, os, html
from First.items import FirstItem
from configparser import ConfigParser
import time, requests
from lxml import etree


class Shuini3Spider(scrapy.Spider):
    name = 'guidao_2'
    start_urls = [
        'http://www.zggdzb.com/cgzb.aspx?&page=1',
        'http://www.zggdzb.com/tlzb.aspx?&page=1',
        'http://www.zggdzb.com/hyzx.aspx?&page=1']

    def __init__(self):
        self.turn_page = True
        self.logger.info('guidao_2.py的日志')
        self.config = ConfigParser()
        self.config.read(os.getcwd() + './spiders/config/config.ini')
        self.items = FirstItem()
        self.items['spider_name'] = 'guidao_2'
        try:
            with open(os.getcwd() + '/spiders/url_deduplication/{}.txt'.format('guidao_2'), 'r') as f:
                self.url_list = f.read().splitlines()
        except Exception as e:
            self.url_list = []

    def parse(self, response):
        self.items['list_url'] = response.url
        if response.status == 200:
            self.logger.info('采集的列表页URL %s', response.url)
            odd_list = response.xpath('//div[@class="list"]/ul/li')
            for node in odd_list:
                try:
                    if response.url.find('cgzb') != -1:
                        self.items['task_name'] = '轨道交通A-38-轨道招标网'
                    elif response.url.find('tlzb') != -1:
                        self.items['task_name'] = '轨道交通A-37-轨道招标网'
                    else:
                        self.items['task_name'] = '轨道交通A-36-轨道招标网'
                    content_url = 'http://www.zggdzb.com/' + node.xpath('./div/a/@href').extract()[0]
                    self.items['content_url'] = content_url
                    title = node.xpath('./div/a/text()').extract()[0]
                    self.items['title'] = title.strip()
                    publish_date = node.xpath('./div[2]/text()').extract()[0]
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
                next_page_num = int(str(response.url).split('=')[-1]) + 1
                next_page_url = response.url.split('=')[0] + '={}'.format(next_page_num)
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
                content_html = re.xpath('//div[@class="list"]')
                html_content = etree.tostring(content_html[0]).decode('utf-8')
                self.items['html_content'] = html.unescape(html_content)
                self.items['pure_content'] = ''.join(re.xpath('//div[@class="list"]/div/p/font/text()')).strip()
                tx = re.xpath('//div[@class="list"]/div/div/text()')[0]
                self.items['origin_source'] = tx.split('\xa0\xa0\r\n\t')[0].replace('文章来源：','')
                self.items['origin_author'] = tx.split('\xa0\xa0\r\n\t')[1].replace('作者：','')
                self.items['update_date'] = int(time.time())
                self.items['title_in_content'] = '1'
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


