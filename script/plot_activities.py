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
  sum_logs = [[[] for _ in range(len(materials))] for _ in range(len(groups))]
  count_submissions = [[] for _ in range(len(groups))]
  active_learners = [[[] for _ in range(len(materials))] for _ in range(len(groups))]
  sum_time_by_user = copy.deepcopy(group_X_material_dict)

  for pset in psets:
    sum_pset_logs = [[[] for _ in range(len(materials))] for _ in range(len(groups))]
    count_pset_submissions = [[] for _ in range(len(groups))]
    sum_pset_time_by_user = copy.deepcopy(group_X_material_dict)

    print_before_stat(pset)

    for group_idx, group in enumerate(groups):
      for username, user_logs in user_pset_logs[group].iteritems():
        if pset in user_logs and is_active(user_logs[pset], submission_type):
          submissions = get_submission_idx(len(user_logs[pset]), submission_type)
          count_submissions[group_idx].append(len(submissions))
          count_pset_submissions[group_idx].append(len(submissions))

          for material_idx, material in enumerate(materials):
            sum_time = 0.0
            for submission_idx in submissions:
              sum_time += user_logs[pset][submission_idx][material]
            # only learners active in a certain material should be counted
            # for the usage(time) of that material
            if sum_time:
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
    yield sum_pset_time_by_user

  print_before_stat('All')
  for group_idx, group in enumerate(groups):
    print_stat(group, sum_logs[group_idx], count_submissions[group_idx], active_learners=active_learners[group_idx])

  yield sum_time_by_user

def gen_stratification(user_profile, tags, user_cohorts, condition=lambda x: True):
  for (header, user) in analytics_util.load_csv_like(user_profile, '\t'):
    result = analytics_util.parse_common_sql(header, user, tags)
    if condition(result[1]) and result[0] not in user_cohorts:
      user_cohorts[result[0]] = 0
    elif not condition(result[1]) and result[0] in user_cohorts:
      user_cohorts[result[0]] += 1 # shift existing layer by one

def _main( ):
  user_listname = sys.argv[1]
  plot_dir = sys.argv[2]
  pset_event_analysis_dir = sys.argv[3]
  user_cohorts = {}
  stratification = sys.argv[4]
  user_profile = sys.argv[5]
  if 'verified' in stratification:
    user_cohort_names = ['honor', 'verify']
    for mode in ['verified', 'honor']: # in reverse order of user_cohort_names
      gen_stratification(user_profile, ['user_id', 'mode'], user_cohorts, lambda x: x == mode)
  elif 'overall_scores_0.5' in stratification:
    boundaries = [0.5]
    user_cohort_names = []
    for lower, upper in zip([0.0]+boundaries, boundaries+[1.01]):
      user_cohort_names.insert(0, 'grade_%f_to_%f' % (lower, upper))
      gen_stratification(user_profile, ['user_id', 'grade'], user_cohorts, lambda x: float(x) >= lower and float(x) < upper)
  else:
    user_cohort_names = ['all']
    gen_stratification(user_profile, ['user_id', 'mode'], user_cohorts)

  if 'nonzero' in stratification:
    user_cohort_names.insert(0, 'grade_is_zero')
    gen_stratification(user_profile, ['user_id', 'grade'], user_cohorts, lambda x: float(x) == 0)

  for user_cohort_index, user_cohort_name in enumerate(user_cohort_names):
    print '\n********** %s learners **********\n' % user_cohort_name
    if not os.path.exists('%s/%s' % (plot_dir, user_cohort_name)):
      os.makedirs('%s/%s' % (plot_dir, user_cohort_name))

    user_lists = {}
    user_pset_logs = {}
    for group in groups:
      user_lists[group] = analytics_util.load_user_infos(
        '%s/%s' % (group, user_listname),
        lambda x: user_cohorts and (x not in user_cohorts or user_cohorts[x] != user_cohort_index) # stratification
      )

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

          pylab.title('materials = %s, pset = %s, time span = %s, stratification = %s' % (
            re.sub('_time', '', material),
            (re.sub('/', '_', psets_pretty[pset_idx]) if pset_idx < len(psets_pretty) else 'all'),
            submission_type,
            user_cohort_name
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
          ax.set_xscale('log')
          plt.xlim((1, 1000000))
          plt.legend()
          '''
          pylab.savefig(
            '%s/%s/%s-%s-%s.pdf' % (
              plot_dir,
              user_cohort_name,
              re.sub('/', '_', psets_pretty[pset_idx]) if pset_idx < len(psets_pretty) else 'all',
              material,
              submission_type
            ),
            format='pdf'
          )
          #plt.close()

if __name__ == '__main__':
  _main( )
