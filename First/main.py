import os
import time
import sys
import subprocess
from configparser import ConfigParser

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
config = ConfigParser()
config.read(os.getcwd() + './config/config.ini')


def task():
    filename_list = []
    for file in os.listdir(os.getcwd()):
        if file.endswith('.py'):
            filename_list.append(file.replace('.py', ''))
    filename_list.pop(filename_list.index('__init__'))
    for filename in filename_list:
        now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        print('{} 任务 [{}] 正在执行中...'.format(now, filename))
        try:
            subprocess.run(['scrapy', 'crawl', '{}'.format(filename)])
        except Exception as e:
            print('Error: {}'.format(e))
        time.sleep(int(config.get('run', 'task_intervals')))


if __name__ == "__main__":
    task()

