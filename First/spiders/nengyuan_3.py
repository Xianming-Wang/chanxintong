# -*- coding: utf-8 -*-
import scrapy, os, html
from First.items import FirstItem
from configparser import ConfigParser
import time, requests
from lxml import etree


class Shuini3Spider(scrapy.Spider):
    name = 'nengyuan_3'
    start_urls = [
        'https://newenergy.in-en.com/corp/Windpower/list1079-1.html'
    ]

    def __init__(self):
        self.turn_page = True
        self.logger.info('nengyuan_3.py的日志')
        self.config = ConfigParser()
        self.config.read(os.getcwd() + './spiders/config/config.ini')
        self.items = FirstItem()
        self.items['spider_name'] = 'nengyuan_3'
        try:
            with open(os.getcwd() + '/spiders/url_deduplication/{}.txt'.format('nengyuan_3'), 'r') as f:
                self.url_list = f.read().splitlines()
        except Exception as e:
            self.url_list = []

    def parse(self, response):
        self.items['list_url'] = response.url
        if response.status == 200:
            self.logger.info('采集的列表页URL %s', response.url)
            odd_list = response.xpath('//ul[@class="infoList"]/li')
            for node in odd_list:
                try:
                    self.items['task_name'] = '能源A-142-国际新能源网'
                    content_url = node.xpath('./div/h5/a/@href').extract()[0]
                    self.items['content_url'] = content_url
                    title = node.xpath('./div/h5/a/text()').extract()[0]
                    self.items['title'] = title.strip()
                    publish_date = node.xpath('./div/div/i/text()').extract()[0]
                    if publish_date.find('小时') != -1 and self.items['content_url'] not in self.url_list:
                        self.items['publish_date'] = self.time_now()
                        self.items['origin_source'] = node.xpath('./div/div/span/text()').extract()[0].replace('来源：', '')
                        self.details_page(content_url)
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
                next_page_num = int(str(response.url).split('-')[-1].replace('.html', '')) + 1
                next_page_url = 'https://newenergy.in-en.com/corp/Windpower/list1079-{}.html'.format(next_page_num)
                yield scrapy.Request(next_page_url, callback=self.parse)
        else:
            self.items['detail_url'] = ''
            self.items['status'] = '采集失败'
            self.items['error'] = '列表页采集失败'

    def time_now(self):
        current = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        return current

    def task_filter(self, current, publish_date):
        p_date = time.strptime(publish_date, '%Y-%m-%d %H:%M')
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


