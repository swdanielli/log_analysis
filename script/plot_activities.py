#! /usr/bin/env python

analytics_util_dir = '/usr/users/swli/program/analytics_util'

import copy
import itertools
import json
import math
import matplotlib
# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pylab
import os.path
import re
import sys
sys.path.append(analytics_util_dir)

import analytics_util

groups = ["dis_no_rec", "no_dis_no_rec", "dis_rec", "no_dis_rec"]
materials = ["forum_time", "pset_time", "recommender_time", "video_time"]
group_X_material_dict = {('%s_%s' % (group, material)): {} for group, material in itertools.product(groups, materials)}
colors = ['b', 'g', 'r', 'k', 'c', 'm', 'y']
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
sub_type_definition = {
  'all': 'First access of pset to the day we grabbed data',
  'all_sub': 'First access of pset to the last answer-submission event',
  'first':  'First access of pset to the first answer-submission event or the day we grabbed data',
  'first_sub': 'First access of pset to the first answer-submission event',
  'other_sub': 'Second answer-submission event to the last answer-submission event'
}
psets_pretty = [
  'Problem_Set_0',
  'Problem_Set_1',
  'Problem_Set_2',
  'Problem_Set_3',
  'Problem_Set_4',
  'Problem_Set_5',
  'Problem_Set_6',
  'Problem_Set_7',
]

def errorplot(xdata, ydata, bins=None, overlay=True):
  '''
  Takes data in the same format as a histogram. Plots it with
  10 bins+errors superimposed
  '''
  if not bins:
    bins = np.arange(10+1)*max(xdata)/10.0
  else:
    bins = np.array(bins)
  points = [ [y for x,y in zip(xdata, ydata) if x < bins[i+1] and x >= bins[i]] for i in range(len(bins)-1)]
 
  means = np.array(map(np.mean, points))
  stddiv = np.array(map(np.std, points))
  n = np.array(map(len,points))

  pylab.errorbar((bins[:-1]+bins[1:])/2, means, yerr=stddiv/np.sqrt(n))
 
  if overlay:
    pylab.scatter(xdata, ydata, alpha=0.1)
    
def is_active(logs, submission_type, material='pset_time'):
  return bool(get_submission_idx(len(logs), submission_type)) and logs[0][material] > 0

def print_line(vec):
  print ' '.join(map(lambda x: x.rjust(24), vec))

def print_before_stat(pset):
  print
  print (psets_pretty[psets.index(pset)] if pset in psets else 'All')
  print_line(['seconds[SE](#learners)', 'forum', 'pset', 'recom', 'video', '#submissions_avg [SE]'])

def print_stat(group, sum_logs, count_submissions, active_learners=None):
  arr = [group]
  for index, sum_log in enumerate(sum_logs):
    if 'no_rec' in group and materials.index('recommender_time') == index:
      arr += ['---(---)']
    else:
      arr += ['%.1f[%.4f](%d)' % (
        float(sum(sum_log))/len(sum_log) if sum_log else 0.0,
        np.std(sum_log)/np.sqrt(len(sum_log)) if sum_log else 0.0,
        len(sum_log) if not active_learners else len(list(set(active_learners[index])))
      )]
  arr += ['%.1f[%.4f]' % (
    float(sum(count_submissions))/len(count_submissions) if count_submissions else 0.0,
    np.std(count_submissions)/np.sqrt(len(count_submissions)) if count_submissions else 0.0
  )]
  print_line(arr)

def get_submission_idx(n_submissions, submission_type):
  if submission_type in ['all']:
    return range(n_submissions)
  elif submission_type in ['all_sub']:
    return range(n_submissions-1)
  elif submission_type in ['first']:
    return [0]
  elif submission_type in ['first_sub']:
    return [0] if n_submissions > 1 else None
  elif submission_type in ['other_sub']:
    return range(1, n_submissions-1)

def compute_accumulated_activities(user_pset_logs, submission_type='all_sub'):
  #sum_logs = np.zeros((len(groups), len(materials)))
  sum_logs = [[[] for _ in range(len(materials))] for _ in range(len(groups))]
  count_submissions = [[] for _ in range(len(groups))]
  #count_submissions = np.zeros(len(groups))
  #count_logs = np.zeros((len(groups), len(materials)))
  active_learners = [[[] for _ in range(len(materials))] for _ in range(len(groups))]
  sum_time_by_user = copy.deepcopy(group_X_material_dict)

  for pset in psets:
    #sum_pset_logs = np.zeros((len(groups), len(materials)))
    sum_pset_logs = [[[] for _ in range(len(materials))] for _ in range(len(groups))]
    #count_pset_submissions = np.zeros(len(groups))
    count_pset_submissions = [[] for _ in range(len(groups))]
    #count_pset_logs = np.zeros((len(groups), len(materials)))
    sum_pset_time_by_user = copy.deepcopy(group_X_material_dict)

    print_before_stat(pset)

    for group_idx, group in enumerate(groups):
      for username, user_logs in user_pset_logs[group].iteritems():
        if pset in user_logs and is_active(user_logs[pset], submission_type):
          submissions = get_submission_idx(len(user_logs[pset]), submission_type)
          #count_submissions[group_idx] += len(submissions)
          #count_pset_submissions[group_idx] += len(submissions)
          count_submissions[group_idx].append(len(submissions))
          count_pset_submissions[group_idx].append(len(submissions))

          for material_idx, material in enumerate(materials):
            sum_time = 0.0
            for submission_idx in submissions:
              sum_time += user_logs[pset][submission_idx][material]
            # only learners active in a certain material should be counted
            # for the usage(time) of that material
            if sum_time:
              '''
              sum_logs[group_idx][material_idx] += sum_time
              sum_pset_logs[group_idx][material_idx] += sum_time
              count_logs[group_idx][material_idx] += 1
              count_pset_logs[group_idx][material_idx] += 1
              '''
              sum_logs[group_idx][material_idx].append(sum_time)
              sum_pset_logs[group_idx][material_idx].append(sum_time)
              active_learners[group_idx][material_idx].append(username)

            # all active users should be plotted
            condition = '%s_%s' % (group, material)
            if username not in sum_time_by_user[condition]:
              sum_time_by_user[condition][username] = 0.0
            sum_time_by_user[condition][username] += sum_time
            sum_pset_time_by_user[condition][username] = sum_time

      print_stat(group, sum_pset_logs[group_idx], count_pset_submissions[group_idx])
      #print_stat(group, sum_pset_logs[group_idx], count_pset_submissions[group_idx], count_pset_logs[group_idx])
    yield sum_pset_time_by_user

  print_before_stat('All')
  for group_idx, group in enumerate(groups):
    print_stat(group, sum_logs[group_idx], count_submissions[group_idx], active_learners=active_learners[group_idx])
    #print_stat(group, sum_logs[group_idx], count_submissions[group_idx], count_logs[group_idx], active_learners=active_learners[group_idx])

  yield sum_time_by_user

def _main( ):
  user_listname = sys.argv[1]
  plot_dir = sys.argv[2]
  pset_event_analysis_dir = sys.argv[3]

  user_lists = {}
  user_pset_logs = {}
  for group in groups:
    user_lists[group] = analytics_util.load_user_infos('%s/%s' % (group, user_listname))

    user_pset_logs[group] = {}
    for username in user_lists[group].keys():
      log_filename = '%s/%s/accumulation-%s' % (group, pset_event_analysis_dir, username)
      if not os.path.isfile(log_filename):
        continue
      user_pset_logs[group][username] = json.load(open(log_filename))

  for submission_type in ['all_sub', 'first_sub', 'other_sub', 'all', 'first']:
    print '\n========== %s ==========\n' % sub_type_definition[submission_type]
    for pset_idx, logs in enumerate(compute_accumulated_activities(user_pset_logs, submission_type)):
      if not any(logs.values()):
        continue

      for material in materials:
        fig = plt.figure()
        plt.clf()
        ax = fig.add_subplot(111)


        (time, scores) = ([], [])
        for group_idx, group in enumerate(groups):
          for username, sum_time in logs['%s_%s' % (group, material)].iteritems():
            time.append(sum_time)
            scores.append(float(user_lists[group][username][0]))
        #ax.scatter(time, scores, c=colors[group_idx], label=group)

        pylab.xscale('log')
        pylab.xlim((1, 1000000))

        pylab.title('materials = %s, pset = %s, time span = %s' % (
          re.sub('_time', '', material),
          (re.sub('/', '_', psets_pretty[pset_idx]) if pset_idx < len(psets_pretty) else 'all'),
          sub_type_definition[submission_type]
        ))
        pylab.xlabel("spent time (seconds)")
        pylab.ylabel("scores")
        errorplot(time, scores, bins=[1,10,100,1000,10000,100000,1000000])
        '''
        # plot by groups
        for group_idx, group in enumerate(groups):
          (time, scores) = ([], [])
          for username, sum_time in logs['%s_%s' % (group, material)].iteritems():
            time.append(sum_time)
            scores.append(float(user_lists[group][username][0]))
          ax.scatter(time, scores, c=colors[group_idx], label=group)
        '''
        #ax.set_xscale('log')
        #plt.xlim((1, 1000000))
        #plt.legend()
        pylab.savefig(
          '%s/%s-%s-%s.pdf' % (
            plot_dir,
            re.sub('/', '_', psets_pretty[pset_idx]) if pset_idx < len(psets_pretty) else 'all',
            material,
            sub_type_definition[submission_type]
          ),
          format='pdf'
        )
        #plt.close()

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
