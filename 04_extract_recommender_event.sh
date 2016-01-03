#!/bin/bash

groups=("dis_no_rec" "no_dis_no_rec" "dis_rec" "no_dis_rec")

for group in "${groups[@]}"
do
  user_list=$group"/user_list"
  user_event_dir=$group"/event_by_user"
  recommender_event_analysis_dir=$group"/recommender_event_analysis"
  mkdir $recommender_event_analysis_dir

  ./script/extract_recommender_event.py $user_list $user_event_dir $recommender_event_analysis_dir
done
