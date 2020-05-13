# -*- coding: utf-8 -*-
import scrapy, os, html
from First.items import FirstItem
import time, requests
from lxml import etree
from configparser import ConfigParser


class Shuini1Spider(scrapy.Spider):
    name = 'shuini_5'
    # allowed_domains = ['ygcg.conch.cn']
    start_urls = ['http://cg.jdsn.com.cn/search?pageNo=1&pageSize=50']

    def __init__(self):
        self.logger.info('shuini_5.py的日志')
        self.config = ConfigParser()
        self.turn_page = True
        self.config.read(os.getcwd() + './spiders/config/config.ini')
        self.items = FirstItem()
        self.items['spider_name'] = 'shuini_5'
        try:
            with open(os.getcwd() + '/spiders/url_deduplication/{}.txt'.format('shuini_5'), 'r') as f:
                self.url_list = f.read().splitlines()
        except Exception as e:
            self.url_list = []

    def parse(self, response):
        self.items['list_url'] = response.url
        if response.status == 200:
            self.logger.info('采集的列表页URL %s', response.url)
            node_list = response.xpath('//div[@class="list-content"]/ul/li')
            for node in node_list:
                try:
                    self.items['task_name'] = '水泥A-6-金隅冀东阳光采购平台'
                    content_url = 'http://cg.jdsn.com.cn' + node.xpath('./a/@href').extract()[0]
                    self.items['content_url'] = content_url
                    title = node.xpath('.//div[@class="bid-name"]/text()').extract()[0]
                    self.items['title'] = title.strip()
                    current = self.time_now()
                    self.details_page(content_url)
                    publish_date = self.items['publish_date']
                    if self.task_filter(current, publish_date):
                        yield self.items
                    else:
                        self.turn_page = False
                        continue
                except Exception as e:
                    self.items['detail_url'] = ''
                    self.items['status'] = '采集失败'
                    self.items['error'] = '列表页解析失败'
                    self.logger.error('列表页内容解析错误 报错信息为： %s' %e )
                    continue
            if self.turn_page:
                next_page_num = int(str(response.url).split('?')[-1].split('&')[0].replace('pageNo=','')) + 1
                next_page_url = 'http://cg.jdsn.com.cn/search?pageNo={}&pageSize=50'.format(next_page_num)
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
                content_html = re.xpath('//div[@class="announce-content"]')
                html_content = etree.tostring(content_html[0]).decode('utf-8')
                publish_date = re.xpath('//div[@class="date"]/text()')
                publish_date = publish_date[0].replace('发布时间：', '')
                self.items['publish_date'] = publish_date
                self.items['html_content'] = html.unescape(html_content)
                self.items['pure_content'] = ''.join(re.xpath('//div[@class="announce-item"]/div/text()')).replace('\xa0', '')
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



