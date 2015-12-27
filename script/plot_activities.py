#! /usr/bin/env python

analytics_util_dir = '/usr/users/swli/program/analytics_util'

import json
import math
import matplotlib
# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os.path
import re
import sys
sys.path.append(analytics_util_dir)

import analytics_util

groups = ["dis_no_rec", "no_dis_no_rec", "dis_rec", "no_dis_rec"]
materials = ["forum_time", "pset_time", "recommender_time", "video_time"]

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

def is_active(logs, no_submission, material='pset_time'):
  if no_submission:
    return len(logs) > 0 and logs[0][material] > 0
  else:
    return len(logs) > 1 and logs[0][material] > 0

def print_line(vec):
  print ' '.join(map(lambda x: x.rjust(14), vec))

def print_before_stat(pset):
  print
  print pset
  print_line([' ', 'forum', 'pset', 'recom', 'video', 'sub_avg'])

def print_stat(group, sum_logs, count_submissions, count_logs):
  print_line(
    [group] +
    map(lambda x: ('%.1f' % x), sum_logs/count_logs) +
    ['%.1f' % (count_submissions/count_logs)]
  )

def compute_accumulated_activities(user_pset_logs, no_submission=False):
  sum_logs = np.zeros((len(groups), len(materials)))
  count_submissions = np.zeros(len(groups))
  count_logs = np.zeros(len(groups))
  for pset in psets:
    sum_pset_logs = np.zeros((len(groups), len(materials)))
    count_pset_submissions = np.zeros(len(groups))
    count_pset_logs = np.zeros(len(groups))

    print_before_stat(pset)

    for group_idx, group in enumerate(groups):
      for user_logs in user_pset_logs[group].values():
        if pset in user_logs and is_active(user_logs[pset], no_submission):
          submissions = (len(user_logs[pset]) if no_submission else len(user_logs[pset])-1)
          count_submissions[group_idx] += submissions
          count_pset_submissions[group_idx] += submissions
          count_logs[group_idx] += 1
          count_pset_logs[group_idx] += 1

          for submission_idx in range(submissions):
            for material_idx, material in enumerate(materials):
              sum_logs[group_idx][material_idx] += user_logs[pset][submission_idx][material]
              sum_pset_logs[group_idx][material_idx] += user_logs[pset][submission_idx][material]

      print_stat(group, sum_pset_logs[group_idx], count_pset_submissions[group_idx], count_pset_logs[group_idx])

  print_before_stat('All')
  for group_idx, group in enumerate(groups):
    print_stat(group, sum_logs[group_idx], count_submissions[group_idx], count_logs[group_idx])

def _main( ):
  user_listname = sys.argv[1]
  plot_dir = sys.argv[2]
  pset_event_analysis_dir = sys.argv[3]

  user_lists = {}
  user_pset_logs = {}
  for group in groups:
    user_lists[group] = sorted(
      analytics_util.load_user_infos('%s/%s' % (group, user_listname)),
      key=lambda x: x[1], reverse=True
    )

    user_pset_logs[group] = {}
    for user_info in user_lists[group]:
      log_filename = '%s/%s/accumulation-%s' % (group, pset_event_analysis_dir, user_info[0])
      if not os.path.isfile(log_filename):
        continue
      user_pset_logs[group][user_info[0]] = json.load(open(log_filename))

  print 'Print only learners with submissions'
  compute_accumulated_activities(user_pset_logs)

  print 'Print all learners with active time > 0'
  compute_accumulated_activities(user_pset_logs, True)

  '''
  for

  quantiztion_bins = None
  if (sys.argv) > 4:
    quantiztion_bins = int(sys.argv[4])

  for l_id in open(mapping):
    l_id = l_id.strip()
    with open('%s/%s' % (word2vec_fea_dir, l_id)) as f:
      try:
        cos_sim_matrix = [[quantiztion(y, quantiztion_bins) for y in x.strip().split('\t')] for x in f.readlines()]
      except ValueError:
        print '%s/%s' % (word2vec_fea_dir, l_id)

      fig = plt.figure()
      plt.clf()
      ax = fig.add_subplot(111)
      res = ax.imshow(np.array(cos_sim_matrix), cmap=plt.cm.Greys_r, interpolation='nearest')
      #res = ax.imshow(np.array(cos_sim_matrix), cmap=plt.cm.jet, interpolation='nearest')
      ax.set_aspect('auto')

      cb = fig.colorbar(res)
      alphabet = '123456789'
      width = len(cos_sim_matrix[0])
      plt.xticks(range(width), alphabet[:width])
      plt.savefig('%s/%s.pdf' % (word2vec_plot_dir, l_id), format='pdf')
      plt.close()
  '''

if __name__ == '__main__':
  _main( )
