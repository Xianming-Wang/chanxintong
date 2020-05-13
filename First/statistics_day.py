import pymongo
import time
import pandas as pd
import os
from other_columns import value_dict
from datetime import datetime
from configparser import ConfigParser
from apscheduler.schedulers.background import BackgroundScheduler


config = ConfigParser()
config.read(os.getcwd() + './spiders/config/config.ini')


def task():
    now = time.strftime('%Y-%m-%d', time.localtime(time.time()))
    time_now = time.strptime(now, '%Y-%m-%d')
    timestamp = int(time.mktime(time_now))

    filePath = os.getcwd() + '/statistics/{}.xls'.format(now)
    client = pymongo.MongoClient(str(config.get('mongodb', 'host')), int(config.get('mongodb', 'port')))

    db = client.admin
    db.authenticate("{}".format(config.get('mongodb', 'username')),
                    "{}".format(config.get('mongodb', 'password')),
                    mechanism='SCRAM-SHA-1')

    db = client.chanxintong_spider
    collection = db.chanxintong

    data_list = []
    for key, value in value_dict.items():
        result = collection.find({'$and': [{"task_name": '{}'.format(key)}, {'update_date': {'$gt': timestamp}}]}).count()
        dic = {
            'counts': result,
            'task_name': key
               }
        data_list.append(dic)

    df = pd.DataFrame(data_list)
    df.to_excel(filePath, encoding='utf-8', index=False, header=True)


def task():
    print(datetime.now())


if __name__ == "__main__":
    scheduler = BackgroundScheduler()

    # scheduler.add_job(task, 'cron', hour=1)
    scheduler.add_job(task, 'interval', days=1)
    scheduler.start()
    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
