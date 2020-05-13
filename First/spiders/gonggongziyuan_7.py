# -*- coding: utf-8 -*-
import scrapy, os, html
from First.items import FirstItem
from configparser import ConfigParser
import time, requests, json
from lxml import etree


class Shuini3Spider(scrapy.Spider):
    name = 'gonggongziyuan_7'
    start_urls = [
        'http://prec.sxzwfw.gov.cn/moreInfoController.do?getMoreResultNoticeInfo&page=1&rows=50'
        '&dateFlag=&tableName=&projectRegion=&sjly=&projectName=&beginReceivetime=&endReceivetime=',
        'http://prec.sxzwfw.gov.cn/moreInfoController.do?getMoreNoticeInfo&page=1&rows=50'
        '&dateFlag=&tableName=&projectRegion=&sjly=&projectName=&beginReceivetime=&endReceivetime='
    ]

    def __init__(self):

        self.logger.info('gonggongziyuan_7.py的日志')
        self.config = ConfigParser()
        self.config.read(os.getcwd() + './spiders/config/config.ini')
        self.items = FirstItem()
        self.items['spider_name'] = 'gonggongziyuan_7'
        try:
            with open(os.getcwd() + '/spiders/url_deduplication/{}.txt'.format('gonggongziyuan_7'), 'r') as f:
                self.url_list = f.read().splitlines()
        except Exception as e:
            self.url_list = []

    def parse(self, response):
        self.items['list_url'] = response.url
        if response.status == 200:
            self.logger.info('采集的列表页URL %s', response.url)
            text = response.text
            json_data = json.loads(text)
            odd_list = json_data.get('obj')
            for node in odd_list:
                try:
                    if response.url.find('getMoreResultNoticeInfo') != -1:
                        self.items['task_name'] = '公共资源交易A-40-山西省'
                    else:
                        self.items['task_name'] = '公共资源交易A-39-山西省'
                    content_url = 'http://prec.sxzwfw.gov.cn/moreInfoController.do?getResultNoticeDetail&url={}&id={}'.format(node.get('URL'),node.get('ID'))
                    self.items['content_url'] = content_url
                    title = node.get('PROJECTNAME')
                    self.items['title'] = title.strip()
                    publish_date = node.get('RECEIVETIME')
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
                content_html = re.xpath('//div[@class="body_main"]')
                html_content = etree.tostring(content_html[0]).decode('utf-8')
                self.items['html_content'] = html.unescape(html_content)
                self.items['pure_content'] = ''.join(re.xpath('//div[@class="body_main"]/p/span/text()'))
                self.items['origin_source'] = ''
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


