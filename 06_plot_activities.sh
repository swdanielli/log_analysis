#!/bin/bash

user_list="user_list"
pset_event_analysis_dir="/pset_event_analysis"
plot_dir='/afs/csail.mit.edu/u/s/swli/public_html/600x_plot_value_transform'

user_profile='/scratch/600x_2015/600x/MITx-6.00.1x_7_3T2015/database/MITx-6.00.1x_7-3T2015-certificates_generatedcertificate-prod-analytics.sql'
stratifications=("all")

for stratification in "${stratifications[@]}"
do
  sub_plot_dir=$plot_dir
  mkdir $sub_plot_dir
  ./script/plot_activities.py $user_list $sub_plot_dir $pset_event_analysis_dir $stratification $user_profile 
done

# all_video_(slot)_x-fold
# lecture_2_video_(slot)_x-fold

#stratification='overall_scores_0.5'
#./script/plot_activities.py $user_list $plot_dir $pset_event_analysis_dir $stratification $user_profile > $log_dir/$stratification

