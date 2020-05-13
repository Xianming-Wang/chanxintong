# -*- coding: utf-8 -*-
import scrapy, os, html
from First.items import FirstItem
from configparser import ConfigParser
import time, requests
from lxml import etree


class Shuini3Spider(scrapy.Spider):
    name = 'gangtie'
    start_urls = [
        'http://www.mcc.com.cn/mcc/_132154/_132568/541fa3cb-1.html'
    ]

    def __init__(self):
        self.turn_page = True
        self.logger.info('gangtie.py的日志')
        self.config = ConfigParser()
        self.config.read(os.getcwd() + './spiders/config/config.ini')
        self.items = FirstItem()
        self.items['spider_name'] = 'gangtie'
        try:
            with open(os.getcwd() + '/spiders/url_deduplication/{}.txt'.format('gangtie'), 'r') as f:
                self.url_list = f.read().splitlines()
        except Exception as e:
            self.url_list = []

    def parse(self, response):
        self.logger.info('采集的列表页URL %s', response.url)
        self.items['list_url'] = response.url
        if response.status == 200:
            odd_list = response.xpath('//div[@class="l_list"]/ul[@class="qs_clear"]/li')
            for node in odd_list:
                try:
                    self.items['task_name'] = '钢铁A-6-中国冶金科工集团'
                    content_url = 'http://www.mcc.com.cn' + node.xpath('./a/@href').extract()[0]
                    self.items['content_url'] = content_url
                    title = node.xpath('./a/text()').extract()[0]
                    self.items['title'] = title.strip()
                    date = node.xpath('./span/text()').extract()[0]
                    publish_date = date[1:-1]
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
                next_page_num = int(str(response.url).split('-')[-1].replace('.html', '')) + 1
                next_page_url = 'http://www.mcc.com.cn/mcc/_132154/_132568/541fa3cb-{}.html'.format(next_page_num)
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
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;'
                      'q=0.8,application/signed-exchange;v=b3',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome'
                          '/75.0.3770.100 Safari/537.36'
        }

        response = requests.get(url, headers=header)
        self.items['detail_url'] = response.url
        if response.status_code == 200:
            re = etree.HTML(response.content)
            try:
                content_html = re.xpath('//div[@class="i_c qs_info "]')
                html_content = etree.tostring(content_html[0]).decode('utf-8')
                self.items['html_content'] = html.unescape(html_content)
                self.items['pure_content'] = ''.join(re.xpath('//div[@class="i_c qs_info "]/p/text()')).strip()
                self.items['origin_source'] = re.xpath('//div[@class="i_ly"]/span[1]/text()')[0]
                self.items['origin_author'] = re.xpath('//div[@class="i_ly"]/span[2]/text()')[0]
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


