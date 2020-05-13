# -*- coding: utf-8 -*-
import scrapy, os, html
from First.items import FirstItem
from configparser import ConfigParser
import time, requests
from lxml import etree


class Shuini3Spider(scrapy.Spider):
    name = 'gonggongziyuan_8'
    start_urls = [
        'https://ggzyfw.beijing.gov.cn/jyxxcggg/index.html',
        'https://ggzyfw.beijing.gov.cn/jyxxggjtbyqs/index.html',
        'https://ggzyfw.beijing.gov.cn/jylcgcjs/index.html'
    ]

    def __init__(self):
        self.turn_page = True
        self.logger.info('gonggongziyuan_8.py的日志')
        self.config = ConfigParser()
        self.config.read(os.getcwd() + './spiders/config/config.ini')
        self.items = FirstItem()
        self.items['spider_name'] = 'gonggongziyuan_8'
        try:
            with open(os.getcwd() + '/spiders/url_deduplication/{}.txt'.format('gonggongziyuan_8'), 'r') as f:
                self.url_list = f.read().splitlines()
        except Exception as e:
            self.url_list = []

    def parse(self, response):
        self.items['list_url'] = response.url
        if response.status == 200:
            self.logger.info('采集的列表页URL %s', response.url)
            odd_list = response.xpath('//ul[@class="article-listjy2"]/li')
            for node in odd_list:
                try:
                    if response.url.find('jyxxcggg') != -1:
                        self.items['task_name'] = '公共资源交易A-34-北京市'
                    elif response.url.find('jyxxggjtbyqs') != -1:
                        self.items['task_name'] = '公共资源交易A-33-北京市'
                    else:
                        self.items['task_name'] = '公共资源交易A-3-北京市'
                    content_url = 'https://ggzyfw.beijing.gov.cn' + node.xpath('./a/@href').extract()[0]
                    self.items['content_url'] = content_url
                    title = ''.join(node.xpath('./a/@title').extract())
                    self.items['title'] = title.strip()
                    publish_date = node.xpath('./div/p/text()').extract()[0].strip()
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
                if response.url.find('_') == -1:
                    next_page_num = response.url.split('.')[0] + '_2.html'
                else:
                    next_page_num = int(response.url.split('_')[-1].resplace('.html','')) + 1
                next_page_url = response.url.split('_')[0] + '_{}.html'.format(next_page_num)
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

        header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cookie': 'clientlanguage=zh_CN',
            'Host': 'ggzyfw.beijing.gov.cn',
            'If-Modified-Since': 'Thu, 30 Apr 2020 09:55:00 GMT',
            'If-None-Match': "5eaaa074-bd2d"
        }
        response = requests.get(url, headers=header)
        self.items['detail_url'] = response.url
        if response.status_code == 200:
            re = etree.HTML(response.text)  # 为什么不能用content而是text
            try:
                content_html = re.xpath('//div[@class="div-article2"]')
                html_content = etree.tostring(content_html[0]).decode('utf-8')
                self.items['html_content'] = html.unescape(html_content)
                self.items['pure_content'] = ''.join(re.xpath('//div[@class="div-article2"]//p/*/*/text()'))
                tx = re.xpath('//div[@class="div-title2"]/text()')[0]
                self.items['origin_source'] = tx.split('信息来源：')[-1].replace('浏览次数：','')
                self.items['origin_author'] = ''
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

