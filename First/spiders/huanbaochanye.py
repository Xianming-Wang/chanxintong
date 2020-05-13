# -*- coding: utf-8 -*-
import scrapy, os, html
from First.items import FirstItem
from configparser import ConfigParser
import time, requests
from lxml import etree


class Shuini3Spider(scrapy.Spider):
    name = 'huanbaochanye'
    start_urls = [
        'https://huanbao.in-en.com/gufei/hazardous/list281-1.html',
        'https://huanbao.in-en.com/environment/valley/list291-1.html',
        'https://huanbao.in-en.com/daqi/AirPurifier/list267-1.html'

    ]

    def __init__(self):
        self.turn_page = True
        self.logger.info('huanbaochanye.py的日志')
        self.config = ConfigParser()
        self.config.read(os.getcwd() + './spiders/config/config.ini')
        self.items = FirstItem()
        self.items['spider_name'] = 'huanbaochanye'
        try:
            with open(os.getcwd() + '/spiders/url_deduplication/{}.txt'.format('huanbaochanye'), 'r') as f:
                self.url_list = f.read().splitlines()
        except Exception as e:
            self.url_list = []

    def parse(self, response):
        self.items['list_url'] = response.url
        if response.status == 200:
            self.logger.info('采集的列表页URL %s', response.url)
            nodes = response.xpath('//ul[@class="infoList"]/li')
            for node in nodes:
                try:
                    if response.url.find('hazardous') != -1:
                        self.items['task_name'] = '环保产业A-93-国际节能环保网'
                    elif response.url.find('environment') != -1:
                        self.items['task_name'] = '环保产业A-92-国际节能环保网'
                    else:
                        self.items['task_name'] = '环保产业A-86-国际节能环保网'
                    content_url = node.xpath('./div/h5/a/@href').extract()[0]
                    self.items['content_url'] = content_url
                    title = node.xpath('./div/h5/a/text()').extract()[0]
                    self.items['title'] = title.strip()
                    origin_source = node.xpath('./div/div/span/text()').extract()[0]
                    self.items['origin_source'] = origin_source.replace('来源：', '')
                    publish_date = node.xpath('./div/div/i/text()').extract()[0]
                    if publish_date.find('小时') != -1 or publish_date.find('分钟') != -1:
                        self.items['publish_date'] = self.time_now()
                        if self.items['content_url'] not in self.url_list:
                            self.details_page(content_url)
                            yield self.items
                        else:
                            continue
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
                next_page_num = int(str(response.url).split('-')[-1].replace('.html','')) + 1
                next_page_url = response.url.split('-')[0] + '-{}.html'.format(next_page_num)
                yield scrapy.Request(next_page_url, callback=self.parse)
        else:
            self.items['detail_url'] = ''
            self.items['status'] = '采集失败'
            self.items['error'] = '列表页采集失败'

    def time_now(self):
        current = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        return current

    def details_page(self, url):
        header = {
            'User-Agent': self.config.get('header', 'user_agent'),
            'Accept': self.config.get('header', 'accept'),
            'Accept-Language': self.config.get('header', 'accept_language')
        }
        response = requests.get(url, headers=header)
        self.items['detail_url'] = response.url
        if response.status_code == 200:
            re = etree.HTML(response.content)  # 为什么不能用content而是text
            try:
                content_html = re.xpath('//div[@class="content"]')
                html_content = etree.tostring(content_html[0]).decode('utf-8')
                self.items['html_content'] = html.unescape(html_content)
                self.items['pure_content'] = ''.join(re.xpath('//div[@class="content"]/p/text()')).strip()
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


