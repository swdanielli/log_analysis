#! /usr/bin/env python

analytics_util_dir = '/usr/users/swli/program/analytics_util'
import copy
import datetime
#import gzip
#import itertools
import json
#import math
import os.path
import re
#import string
#import subprocess
import sys
sys.path.append(analytics_util_dir)

import analytics_util

start_date = datetime.date(2015, 7, 14)
end_date = datetime.date(2015, 12, 22)

# first attempt ->
#   spent_time in videos/pset/recommender/forum

# first attempt to last submission (time)

# n_submissions
# n_hints
# grade (?)

# =============================================
# others
# not pset, don't sort
# n_problem_check
# n_problem_grade

psets = [
  'Week_1/Problem_Set_1',
  'Week_2/Basic_Problem_Set_1',
  'Week_2/Problem_Set_2',
  'sp13_Week_3/sp13_Problem_Set_3',
  'Week_4/Problem_Set_4',
  'e6a58de28661441fa8f4156ea0306cc1', # Week_5
  'Week_6/Problem_Set_5',
  'Week_10/Problem_Set_6',
]
max_unresponse_time = 30 * 60 # events separated by time > this threshold are treated as independent events
max_pset_session = 120 * 60 # pset events separated by time > this threshold are treated as independent events

def increment_time_diff_by_materials(prev_action_time, time, temp_statistics, pset_id, type_id=''):
  if prev_action_time and type_id in prev_action_time:
    time_diff = analytics_util.time_diff(prev_action_time.values()[0], time)
    if (
      ('pset_time' in prev_action_time and time_diff < max_pset_session) or
      ('pset_time' not in prev_action_time and time_diff < max_unresponse_time)
    ):
      temp_statistics[pset_id][prev_action_time.keys()[0]] += time_diff

def filter_events(event_type):
  if (
    'page_close' in event_type or
    'seq_' in event_type or
    'video' in event_type or
    'forum' in event_type or
    'problem' in event_type or
    'mit.recommender' in event_type or
    'Problem_Set' in event_type or
    'e6a58de28661441fa8f4156ea0306cc1' in event_type
  ):
    return False
  return True

def check_pset(event):
  try:
    for pset_index in range(len(psets)):
      if psets[pset_index] in event['referer'] or psets[pset_index] in event['page']:
        return pset_index
  except TypeError:
    return -1
  return -1

def is_pset_event(event_type):
  return not ('video' in event_type or 'forum' in event_type or 'mit.recommender' in event_type)

def cal_score(correct_map):
  score = 0.0
  for grade_result in correct_map.values():
    score += (grade_result['npoints'] if grade_result['npoints'] else 0.0)
  return score

def _main( ):
  user_list = sys.argv[1]
  user_event_dir = sys.argv[2]
  pset_event_analysis_dir = sys.argv[3]

  users = analytics_util.load_users(user_list)

  for single_date in ['accumulation']:
    for user in users:
      event_filename = '%s/%d/%s' % (user_event_dir, user, single_date)
      if not os.path.isfile(event_filename):
        continue

      '''
        pset_statistics:
          pset_id: [
            {}, # submission 0 to 1
            {}, # submission 1 to 2
            {statistics} # last submission to first time access the next problem/or EOF
            ... # we can add submission 0 to last
          ]
                                  <- 30m ->
          first pset -- another event -- other events -- close pset session
                closest pset event <------- 120m -------> close
      '''
      pset_statistics = {}
      statistics = {
        'video_time': 0.0,
        'forum_time': 0.0,
        'pset_time': 0.0,
        'recommender_time': 0.0
      }
      '''
        submission_history
          pset_id: {
            problem_id: {
              'max_grade': ?
              'scores': []
            },
            ...
          }
      '''
      submission_history = {}
      temp_statistics = {}
      prev_action_time = {}
      prev_pset_action_time = None
      pset_index = -1 # -1: not in pset session
      in_pset_session = False

      events = analytics_util.load_time_sorted_event(
        event_filename,
        ['mit.recommender', 'video', 'page_close', 'seq_', 'forum', 'e6a58de28661441fa8f4156ea0306cc1', 'Problem_Set_'],
        lambda x: 'event_type' not in x or filter_events(x['event_type'])
      )

      for event in events:
        event_pset_index = check_pset(event)
        event_type = event['event_type']
        if is_pset_event(event_type) and event_pset_index >= 0: #pset
          if event_pset_index != pset_index:
            pset_index = event_pset_index
            if psets[pset_index] not in pset_statistics:
              pset_statistics[psets[pset_index]] = []
              submission_history[psets[pset_index]] = {}
              temp_statistics[psets[pset_index]] = copy.deepcopy(statistics)
          else:
            if event_type == 'problem_check' and event['event_source'] == 'server': # submission
              if prev_pset_action_time:
                temp_statistics[psets[pset_index]]['pset_time'] += analytics_util.time_diff(prev_pset_action_time, event['time'])
              else:
                temp_statistics[psets[pset_index]]['pset_time'] += max_pset_session
              pset_statistics[psets[pset_index]].append(copy.deepcopy(temp_statistics[psets[pset_index]]))
              temp_statistics[psets[pset_index]] = copy.deepcopy(statistics)
              try:
                event_info = event['event']
                problem_id = event_info['problem_id']
                if problem_id not in submission_history[psets[pset_index]]:
                  submission_history[psets[pset_index]][problem_id] = {
                    'max_grade': event_info['max_grade'],
                    'scores': []
                  }
                #submission_history[psets[pset_index]][problem_id]['scores'].append(event_info['grade'])
                submission_history[psets[pset_index]][problem_id]['scores'].append(cal_score(event_info['correct_map']))
              except KeyError:
                print event
                raise KeyError
            else:
              increment_time_diff_by_materials(prev_action_time, event['time'], temp_statistics, psets[pset_index], 'pset_time')
              if 'page_close' in event_type:
                prev_action_time = {}
                continue
#           except TypeError:
#            print event
#            raise TypeError

          prev_action_time = {'pset_time': event['time']}
          in_pset_session = True
          prev_pset_action_time = event['time']
        elif in_pset_session:
          time_diff = analytics_util.time_diff(prev_pset_action_time, event['time'])
          if time_diff > max_pset_session:
            in_pset_session = False
            prev_action_time = {}
            prev_pset_action_time = None
          elif 'page_close' in event_type or 'seq_' in event_type:
            increment_time_diff_by_materials(prev_action_time, event['time'], temp_statistics, psets[pset_index])
            if 'page_close' in event_type:
              prev_action_time = {}
            elif prev_action_time:
              prev_action_time = {prev_action_time.keys()[0]: event['time']}
          elif 'video' in event_type:
            increment_time_diff_by_materials(prev_action_time, event['time'], temp_statistics, psets[pset_index], 'video_time')
            prev_action_time = {'video_time': event['time']}
          elif 'forum' in event_type:
            increment_time_diff_by_materials(prev_action_time, event['time'], temp_statistics, psets[pset_index], 'forum_time')
            prev_action_time = {'forum_time': event['time']}
          elif 'mit.recommender' in event_type:
            increment_time_diff_by_materials(prev_action_time, event['time'], temp_statistics, psets[pset_index], 'recommender_time')
            prev_action_time = {'recommender_time': event['time']}

      for pset_id, stat in temp_statistics.iteritems():
        pset_statistics[pset_id].append(copy.deepcopy(stat))

      analytics_util.dump_data_json(
        '%s/%s-%s' % (pset_event_analysis_dir, single_date, user),
        pset_statistics
      )
      analytics_util.dump_data_json(
        '%s/%s-%s' % (pset_event_analysis_dir, 'submission_hist', user),
        submission_history
      )

if __name__ == '__main__':
  _main( )
