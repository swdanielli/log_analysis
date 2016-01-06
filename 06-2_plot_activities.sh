#!/bin/bash

user_list="user_list"
pset_event_analysis_dir="/pset_event_analysis"
plot_dir='/afs/csail.mit.edu/u/s/swli/public_html/600x_plot'
log_dir='06_log'

user_profile='user_profile'

. /usr/users/swli/swli_env/bin/activate

for part in "all" "lecture_2"
do
  if [ "$part" == "all" ]; then
    cat dis_*/video_event_analysis/accumulation no_dis_*/video_event_analysis/accumulation > user_profile
  else
    cat dis_*/video_event_analysis/$part/accumulation no_dis_*/video_event_analysis/$part/accumulation > user_profile
  fi

  for mode in "n_played_videos" "watch_time" "covered_video_time" "watch_2_cover" "f_seek" "b_seek"
  do
    for n_folds in "2-folds" "4-folds" "5-folds" "10-folds"
    do
      stratification=$part"_video_"$mode"_"$n_folds
      sub_plot_dir=$plot_dir/$stratification
      mkdir $sub_plot_dir
      ./script/plot_activities.py $user_list $sub_plot_dir $pset_event_analysis_dir $stratification $user_profile > $log_dir/$stratification
    done
  done

  cat dis_*/prac_pset_event_analysis/$part/accumulation no_dis_*/prac_pset_event_analysis/$part/accumulation > user_profile

  for mode in "n_attempts" "unique_attempted_problem" "n_attempts_per_problem" "scores" "scores_normalized_by_week" "normalized_scores" "avg_normalized_scores"
  do
    for n_folds in "2-folds" "4-folds" "5-folds" "10-folds"
    do
      stratification=$part"_prac_pset_"$mode"_"$n_folds
      sub_plot_dir=$plot_dir/$stratification
      mkdir $sub_plot_dir
      ./script/plot_activities.py $user_list $sub_plot_dir $pset_event_analysis_dir $stratification $user_profile > $log_dir/$stratification
    done
  done
done


