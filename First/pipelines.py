# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo, os
import pandas as pd
from .other_columns import value_dict
from configparser import ConfigParser
from sqlalchemy import create_engine
config = ConfigParser()
config.read(os.getcwd() + './config/config.ini')


class FirstPipeline(object):

    def __init__(self):
        self.engine = create_engine('mysql+pymysql://{}:{}@{}/{}?charset=utf8'.format(
            config.get('mysqldb', 'username'),
            config.get('mysqldb', 'password'),
            config.get('mysqldb', 'host'),
            config.get('mysqldb', 'database'),
        ))
        client = pymongo.MongoClient(str(config.get('mongodb', 'host')), int(config.get('mongodb', 'port')))
        # client = pymongo.MongoClient('192.168.1.241', 27017)
        db = client.admin
        db.authenticate("{}".format(config.get('mongodb', 'username')),
                        "{}".format(config.get('mongodb', 'password')),
                        mechanism='SCRAM-SHA-1')
        # db.authenticate('admin', 'dnM9tpSkyXXRKNGXsl4AoxOOP5BS74WA4lSlf3RM', mechanism='SCRAM-SHA-1')
        db = client.chanxintong_spider
        self.collection = db.chanxintong
        # self.collection.insert({"name": "zhangsan", "age": 18})

    def process_item(self, item, spider):
        values = value_dict.get(item['task_name'])
        if values:
            item['column'] = values.get('column', '')
            item['origin_deptment'] = values.get('origin_deptment', '')
            item['origin_place'] = values.get('origin_place', '')
            item['origin_type'] = values.get('origin_type', '')
            item['industry_class'] = values.get('industry_class', '')
        else:
            item['column'] = ''
            item['origin_deptment'] = ''
            item['origin_place'] = ''
            item['origin_type'] = ''
            item['industry_class'] = ''

        status = dict()
        status['spider_name'] = item['spider_name']
        status['date'] = item['publish_date']
        status['list_url'] = item['list_url']
        status['detail_url'] = item['detail_url']
        status['status'] = item['status']
        status['error'] = item['error']
        dataframe = pd.DataFrame(status, index=[0])
        try:
            dataframe.to_sql('spider', con=self.engine, index=False, if_exists='append')
        except Exception as e:
            print(e)
        try:
            self.collection.insert(dict(item))
        except Exception as e:
            print(e)
        with open(os.getcwd() + '/spiders/url_deduplication/{}.txt'.format(spider.name), 'a') as f:
            f.writelines(item['content_url'] + '\n')

        return item
