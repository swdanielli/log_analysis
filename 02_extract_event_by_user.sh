#!/bin/bash

base_dir='/scratch/600x_2015/600x/MITx-6.00.1x_7_3T2015'
event_dir=$base_dir"/events"
event_prefix=$event_dir"/MITx_6.00.1x_7_3T2015-events-"
event_suffix=".log.gz"

groups=("dis_no_rec" "no_dis_no_rec" "dis_rec" "no_dis_rec")

for group in "${groups[@]}"
do
  user_list=$group"/user_list"
  user_event_dir=$group"/event_by_user"
  mkdir $user_event_dir

  ./script/extract_event_by_user.py $event_prefix $event_suffix $user_list $user_event_dir
done
