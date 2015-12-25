#! /usr/bin/env python

analytics_util_dir = '/usr/users/swli/program/analytics_util'
#import copy
import datetime
import gzip
import json
import os.path
import re
#import string
#import subprocess
import sys
sys.path.append(analytics_util_dir)

import analytics_util

def write_event(event_handlers, user_id, user_event_dir, user_event_fname, event):
  if user_id not in event_handlers:
    if user_event_fname == 'accumulation':
      os.makedirs('%s/%s' % (user_event_dir, str(user_id)))
    event_handlers[user_id] = open('%s/%s/%s' % (user_event_dir, str(user_id), user_event_fname), 'w')
  event_handlers[user_id].write(event)

def _main( ):
  event_prefix = sys.argv[1]
  event_suffix = sys.argv[2]
  user_list = sys.argv[3]
  user_event_dir = sys.argv[4]

  user_per_batch = 10000
  start_date = datetime.date(2015, 7, 14)
  end_date = datetime.date(2015, 12, 22)
  all_users = analytics_util.load_users(user_list)

  for users in analytics_util.chunks(all_users, user_per_batch):
    f_accumulate_events = {}
    for single_date in analytics_util.date_range_gen(start_date, end_date):
      event_name = '%s%s%s' % (event_prefix, str(single_date), event_suffix)
      if not os.path.isfile(event_name):
        continue
      f_date_events = {}
      for line in gzip.open(event_name):
        data = json.loads(line)
        try:
          user_id = data['context']['user_id']
          if user_id in users:
            write_event(f_accumulate_events, user_id, user_event_dir, 'accumulation', line)
            write_event(f_date_events, user_id, user_event_dir, str(single_date), line)
        except KeyError:
          print line

      for f_date_event in f_date_events.values():
        f_date_event.close()

    for f_accumulate_event in f_accumulate_events.values():
      f_accumulate_event.close()

if __name__ == '__main__':
  _main( )
