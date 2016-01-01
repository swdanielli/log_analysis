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
import operator
import os.path
import re
from scipy.stats import ttest_ind
import sys
sys.path.append(analytics_util_dir)

import analytics_util

groups = ["dis_no_rec", "no_dis_no_rec", "dis_rec", "no_dis_rec"]
hyper_groups = [
  {'dis': [0, 2]},
  {'no_dis': [1, 3]},
  {'rec': [2, 3]},
  {'no_rec': [0, 1]},
]

materials = ["forum_time", "pset_time", "recommender_time", "video_time"]
group_X_material_dict = {('%s_%s' % (group, material)): {} for group, material in itertools.product(groups, materials)}
colors = ['b', 'g', 'r', 'k', 'c', 'm', 'y']
psets = [
#  'Week_1/Problem_Set_1',
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
#  'Problem_Set_0',
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
  return bool(get_submission_idx(len(logs), submission_type)) and logs[0][material] > 10

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
      arr += ['%.4f[%.4f](%d)' % (
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

def remove_outliers(sum_logs, count_submissions):
  min_pset_time = 7 * 60 * 30 # spend at least 20 minutes
  max_pset_time = 7 * 60 * 60 * 44 # spend at most 48 hours
  for group_idx in range(len(groups)):
    for username in sum_logs[group_idx].keys():
      pset_time = sum_logs[group_idx][username][materials.index('pset_time')]
      if pset_time > max_pset_time or pset_time < min_pset_time:
        del sum_logs[group_idx][username]
        del count_submissions[group_idx][username]

def log_time(sum_logs):
  for group_idx in range(len(groups)):
    for username in sum_logs[group_idx].keys():
      for material_idx in range(len(materials)):
        time = sum_logs[group_idx][username][material_idx]
        sum_logs[group_idx][username][material_idx] = math.log(time) if time else 0.0

def compute_accumulated_activities(user_pset_logs, submission_type='all_sub'):
#  sum_logs = [[{} for _ in range(len(materials))] for _ in range(len(groups))]
  sum_logs = [{} for _ in range(len(groups))]
  count_submissions = [{} for _ in range(len(groups))]
  #active_learners = [[[] for _ in range(len(materials))] for _ in range(len(groups))]
  sum_time_by_user = copy.deepcopy(group_X_material_dict)

  for group_idx, group in enumerate(groups):
    for username in user_pset_logs[group].keys():
      count_submissions[group_idx][username] = 0.0
      sum_logs[group_idx][username] = [0.0 for _ in range(len(materials))]

  for pset in psets:
    sum_pset_logs = [[[] for _ in range(len(materials))] for _ in range(len(groups))]
    count_pset_submissions = [[] for _ in range(len(groups))]
    sum_pset_time_by_user = copy.deepcopy(group_X_material_dict)

#    print_before_stat(pset)

    for group_idx, group in enumerate(groups):
      for username, user_logs in user_pset_logs[group].iteritems():
        if pset in user_logs and is_active(user_logs[pset], submission_type):
          submissions = get_submission_idx(len(user_logs[pset]), submission_type)
          if username in count_submissions[group_idx]:
            count_submissions[group_idx][username] += len(submissions)
          #count_submissions[group_idx].append(len(submissions))
          count_pset_submissions[group_idx].append(len(submissions))

          for material_idx, material in enumerate(materials):
            sum_time = 0.0
            for submission_idx in submissions:
              sum_time += user_logs[pset][submission_idx][material]
            # only learners active in a certain material should be counted
            # for the usage(time) of that material
            if sum_time:
              if username in sum_logs[group_idx]:
                sum_logs[group_idx][username][material_idx] += sum_time
              #sum_logs[group_idx][material_idx].append(sum_time)
              sum_pset_logs[group_idx][material_idx].append(sum_time)
              #active_learners[group_idx][material_idx].append(username)

            # all active users should be plotted
            condition = '%s_%s' % (group, material)
            if username not in sum_time_by_user[condition]:
              sum_time_by_user[condition][username] = 0.0
            sum_time_by_user[condition][username] += sum_time
            sum_pset_time_by_user[condition][username] = sum_time
        else:
          if username in count_submissions[group_idx]:
            del count_submissions[group_idx][username]
            del sum_logs[group_idx][username]
#      print_stat(group, sum_pset_logs[group_idx], count_pset_submissions[group_idx])
#    for hyper_group in hyper_groups:
#      (logs, counts) = ([[] for _ in range(len(materials))], [])
#      for index in hyper_group.values()[0]:
#        counts += count_pset_submissions[index]
#        for material_idx in range(len(materials)):
#          logs[material_idx] += sum_pset_logs[index][material_idx]
#      print_stat(hyper_group.keys()[0], logs, counts)

    yield sum_pset_time_by_user

  remove_outliers(sum_logs, count_submissions)

  log_time(sum_logs)

  print_before_stat('All')
  for group_idx, group in enumerate(groups):
#    print max(zip(*(sum_logs[index].values()))[1])
#    print min(zip(*(sum_logs[index].values()))[1])

    print_stat(group, zip(*(sum_logs[group_idx].values())), count_submissions[group_idx].values())
    #print_stat(group, sum_logs[group_idx], count_submissions[group_idx], active_learners=active_learners[group_idx])

  for group in ["dis_rec", "no_dis_rec"]:
    t, p = ttest_ind(
      zip(*(sum_logs[groups.index(group)].values()))[materials.index('pset_time')],
      zip(*(sum_logs[groups.index("no_dis_no_rec")].values()))[materials.index('pset_time')],
      equal_var=False
    )
    print "%s vs. no_dis_no_rec, ttest_ind: t = %g p = %g" % (group, t, p)

  for hyper_group in hyper_groups:
    (logs, counts) = ([() for _ in range(len(materials))], [])
    for index in hyper_group.values()[0]:
      counts += count_submissions[index].values()
      for material_idx in range(len(materials)):
        logs[material_idx] += zip(*(sum_logs[index].values()))[material_idx]
    print_stat(hyper_group.keys()[0], logs, counts)

  yield sum_time_by_user

def gen_stratification(user_profile, tags, user_cohorts, condition=lambda x: True):
  for (header, user) in analytics_util.load_csv_like(user_profile, '\t'):
    result = analytics_util.parse_common_sql(header, user, tags)
    stratify_users(user_cohorts, result[0], condition(result[1]))

def stratify_users(user_cohorts, users, is_condition):
    if is_condition and users not in user_cohorts:
      user_cohorts[users] = 0
    elif not is_condition and users in user_cohorts:
      user_cohorts[users] += 1 # shift existing layer by one

def gen_stratification_sorted_list(user_cohorts, user_lists, condition=lambda x: True):
  l = len(user_lists)
  for index, user in enumerate(user_lists):
    stratify_users(user_cohorts, user, condition(float(index)/l))

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
  elif 'overall_scores' in stratification:
    if '0.6_overall_scores' in stratification:
      boundaries = [0.6]
    elif '0.2_0.4_0.6_0.8_overall_scores' in stratification:
      boundaries = [0.2, 0.4, 0.6, 0.8]
    user_cohort_names = []
    for lower, upper in zip([0.0]+boundaries, boundaries+[1.01]):
      user_cohort_names.insert(0, 'grade_%f_to_%f' % (lower, upper))
      gen_stratification(user_profile, ['user_id', 'grade'], user_cohorts, lambda x: float(x) >= lower and float(x) < upper)
  elif 'video' in stratification or 'prac_pset' in stratification:
    active_users = []
    user_lists = []
    for group in groups:
      active_users += analytics_util.load_user_infos('%s/%s' % (group, user_listname)).keys()
    is_outliers = lambda x: False

    if 'watch_2_cover' in stratification:
      is_outliers = lambda x: x > 10
    if 'video' in stratification:
      mode = re.match('.*?video_(.*)_\d+-folds', stratification).group(1)
    elif 'prac_pset' in stratification:
      mode = re.match('.*?prac_pset_(.*)_\d+-folds', stratification).group(1)

    for (header, user) in analytics_util.load_csv_like(user_profile, '\t'):
      result = analytics_util.parse_common_sql(header, user, ['user_id', mode])
      if (result[0] in active_users) and (not is_outliers(result[1])):
        try:
          user_lists.append((result[0], float(result[1])))
        except ValueError:
          print result[1]
          pass
    user_lists = [x[0] for x in sorted(user_lists, key=operator.itemgetter(1))]

    n_folds = int(re.match('.*_(\d+)-folds', stratification).group(1))
    boundaries = [x / float(n_folds) for x in range(1, n_folds)]
    user_cohort_names = []
    for lower, upper in zip([0.0]+boundaries, boundaries+[1.0]):
      user_cohort_names.insert(0, '%s_%dth_to_%dth' % (mode, int(lower*100), int(upper*100)))
      gen_stratification_sorted_list(user_cohorts, user_lists, lambda x: x >= lower and x < upper)

    if 'all' in stratification:
      user_cohort_names = map(lambda x: x + ' in all lectures', user_cohort_names)
    elif 'lecture_2' in stratification:
      user_cohort_names = map(lambda x: x + ' in lecture 2', user_cohort_names)
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

        continue # TODO

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
