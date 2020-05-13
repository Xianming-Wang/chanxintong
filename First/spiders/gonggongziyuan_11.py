# -*- coding: utf-8 -*-
import scrapy, os, html
from First.items import FirstItem
from configparser import ConfigParser
import time, requests,re
from lxml import etree


class Shuini3Spider(scrapy.Spider):
    name = 'gonggongziyuan_11'
    start_urls = [
        'http://ggzyjy.gansu.gov.cn/f/newprovince/annogoods/getAnnoList?pageNo=1&pageSize=20&area=620000'
        '&prjpropertynewI=I&prjpropertynewA=A&prjpropertynewD=D&prjpropertynewC=C&prjpropertynewB=B'
        '&prjpropertynewE=E&projectname='
    ]

    def __init__(self):
        self.turn_page = True
        self.logger.info('gonggongziyuan_11.py的日志')
        self.config = ConfigParser()
        self.config.read(os.getcwd() + './spiders/config/config.ini')
        self.items = FirstItem()
        self.items['spider_name'] = 'gonggongziyuan_11'
        try:
            with open(os.getcwd() + '/spiders/url_deduplication/{}.txt'.format('gonggongziyuan_11'), 'r') as f:
                self.url_list = f.read().splitlines()
        except Exception as e:
            self.url_list = []

    def parse(self, response):
        self.items['list_url'] = response.url
        if response.status == 200:
            self.logger.info('采集的列表页URL %s', response.url)
            odd_list = response.xpath('//dl[@class="sDisclosurLeftConDetailList"]/dd')
            for node in odd_list:
                try:
                    self.items['task_name'] = '公共资源交易A-17-甘肃省'
                    content_url = 'http://ggzyjy.gansu.gov.cn' + node.xpath('./p/a/@href').extract()[0]
                    self.items['content_url'] = content_url
                    title = ''.join(node.xpath('./p/a/text()').extract())
                    self.items['title'] = title.strip()
                    publish_date = node.xpath('./i/text()').extract()[0].strip()
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
                next_page_num = int(response.url.split('pageNo=')[-1].split('&')[0]) + 1
                next_page_url = 'http://ggzyjy.gansu.gov.cn/f/newprovince/annogoods/getAnnoList?pageNo={}&pageSize=20' \
                                '&area=620000&prjpropertynewI=I&prjpropertynewA=A&prjpropertynewD=D&prjpropertynewC=C' \
                                '&prjpropertynewB=B&prjpropertynewE=E&projectname='.format(next_page_num)
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
        code = url.split('/')[-2]
        new_url = 'http://ggzyjy.gansu.gov.cn/f/newprovince/tenderproject/flowBidpackage?tenderprojectid={}' \
                  '&bidpackages=&projectType=D03'.format(code)
        response = requests.get(new_url, headers=header)
        self.items['detail_url'] = response.url
        if response.status_code == 200:
            try:
                self.items['html_content'] = response.text
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

