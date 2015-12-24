#! /usr/bin/env python

import numpy as np
import math
import matplotlib
# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sys

def quantiztion(val, quantiztion_bins=None):
  if math.isnan(float(val)):
    return 0
  elif quantiztion_bins:
    val = int(float(val)*quantiztion_bins)/float(quantiztion_bins-1)
    return 1 if val > 1 else val
  else:
    return float(val)

def _main( ):
  mapping = sys.argv[1]
  word2vec_fea_dir = sys.argv[2]
  word2vec_plot_dir = sys.argv[3]
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

if __name__ == '__main__':
  _main( )
