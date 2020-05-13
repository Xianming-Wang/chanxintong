from datetime import datetime
import os
import sys
import subprocess


sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    final_start = datetime.now()
    next_time_hour = final_start.hour
    next_time_min = final_start.minute
    next_time_sec = final_start.second
    while True:
        if datetime.now().hour == next_time_hour and datetime.now().minute == next_time_min \
                and datetime.now().second == next_time_sec:
            print('{}   main.py正在执行.....'.format(datetime.now()))
            print('-*-' * 10)
            try:
                subprocess.run(['python', '{}\\main.py'.format(os.path.dirname(__file__))])
            except Exception as e:
                print('Error:  {}'.format(e))
            next_time_hour += 1
