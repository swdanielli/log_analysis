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

def check_pset(event, considered_ids):
  for considered_id in considered_ids:
    if check_page(event, considered_id):
      return considered_id
  return None

def check_page(event, check_string):
  try:
    return True if (check_string in event['referer'] or check_string in event['page']) else False
  except TypeError:
    return False

def _main( ):
  user_list = sys.argv[1]
  user_event_dir = sys.argv[2]
  prac_pset_event_analysis_dir = sys.argv[3]
  part_of_lecture = sys.argv[4]
  considered_ids = [] # lecture_id

  if 'lecture_2' in part_of_lecture:
    considered_ids.append('ed0d1659290e4afea1d3d13d1da22392')
  if 'all' in part_of_lecture:
    considered_ids.append('a3deaa6114824f43bce877dffe37cdd6')
    considered_ids.append('ed0d1659290e4afea1d3d13d1da22392')
    considered_ids.append('videosequence:Lecture_3')
    considered_ids.append('videosequence:Lecture_4')
    considered_ids.append('videosequence:Lecture_5')
    considered_ids.append('videosequence:Lecture_6')
    considered_ids.append('videosequence:Lecture_7')
    considered_ids.append('5a6015f580a94bb59799d30edd72d4ea')
    considered_ids.append('videosequence:Lecture_8')
    considered_ids.append('videosequence:Lecture_9')
    considered_ids.append('videosequence:Lecture_10')
    considered_ids.append('videosequence:Lecture_11')
    considered_ids.append('videosequence:Lecture_19')

  users = analytics_util.load_users(user_list)

  for single_date in ['accumulation']:
    f_o = open('%s/%s' % (prac_pset_event_analysis_dir, single_date), 'w')
    f_o.write('\t'.join(['user_id', 'n_attempts', 'unique_attempted_problem', 'n_attempts_per_problem', 'scores', 'scores_normalized_by_week', 'normalized_scores', 'avg_normalized_scores']) + '\n')
    user_stat = {}

    for user in users:
      event_filename = '%s/%d/%s' % (user_event_dir, user, single_date)
      if not os.path.isfile(event_filename):
        continue
      pset_statistics = {}
      '''
        submission_history
          lecture_id: {
            problem_id: {
              'max_grade': ?
              'grade': []
            },
            ...
          }
      '''
      submission_history = {}

      events = analytics_util.load_time_sorted_event(
        event_filename,
        ['problem_check'],
        lambda x: 'event_type' not in x,
        must_have=considered_ids
      )

      for event in events:
        event_prac_pset = check_pset(event, considered_ids)
        if event_prac_pset not in submission_history:
          submission_history[event_prac_pset] = {}
        if event_prac_pset and event['event_type'] == 'problem_check' and event['event_source'] == 'server': # submission
          #try:
            event_info = event['event']
            problem_id = event_info['problem_id']
            if problem_id not in submission_history[event_prac_pset]:
              submission_history[event_prac_pset][problem_id] = {
                'max_grade': event_info['max_grade'],
                'grade': [],
                'normalized_max_grade': 1,
                'normalized_grade': []
              }
            submission_history[event_prac_pset][problem_id]['grade'].append(event_info['grade'])
            submission_history[event_prac_pset][problem_id]['normalized_grade'].append(float(event_info['grade'])/event_info['max_grade'])
          #except KeyError:
          #  print event
          #  raise KeyError
      user_stat[user] = submission_history
      #analytics_util.dump_data_json('1234', submission_history)

    max_grade = {}
    for submission_history in user_stat.values():
      for lecture_id, problem_stat in submission_history.iteritems():
        if lecture_id not in max_grade:
          max_grade[lecture_id] = {}
        for problem_id, info in problem_stat.iteritems():
          max_grade[lecture_id][problem_id] = info['max_grade']
    #print max_grade

    max_grade = {lecture_id: sum(problem_stat.values()) for lecture_id, problem_stat in max_grade.iteritems()}
    print max_grade
    for user_id, submission_history in user_stat.iteritems():
      # user_id
      f_o.write('%d\t' % user_id)
      n_attempts = 0
      unique_attempted_problem = 0
      scores = 0.0
      scores_normalized_by_week = 0.0
      normalized_scores = 0.0
      for lecture_id, problem_stat in submission_history.iteritems():
        lecture_score = 0.0
        unique_attempted_problem += len(problem_stat.keys())
        for stat in problem_stat.values():
          n_attempts += len(stat['grade'])
          scores += max(stat['grade'])
          lecture_score += max(stat['grade'])
          normalized_scores += max(stat['normalized_grade'])
        scores_normalized_by_week += float(lecture_score)/max_grade[lecture_id]
      # n_attempts
      f_o.write('%d\t' % n_attempts)
      # unique_attempted_problem
      f_o.write('%d\t' % unique_attempted_problem)
      # n_attempts_per_problem
      f_o.write('%f\t' % (float(n_attempts)/unique_attempted_problem if unique_attempted_problem else 0.0))
      # scores
      f_o.write('%f\t' % scores)
      # scores_normalized_by_week
      f_o.write('%f\t' % scores_normalized_by_week)
      # normalized_scores -> score/max_score
      f_o.write('%f\t' % normalized_scores)
      # avg_normalized_scores
      f_o.write('%f\n' % (normalized_scores/unique_attempted_problem if unique_attempted_problem else 0.0))

if __name__ == '__main__':
  _main( )
