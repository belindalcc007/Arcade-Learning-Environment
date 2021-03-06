import numpy as np
import keras as K
import tensorflow as tf
import copy as cp
from misc_utils import my_kld
import time, sys, os
from scipy import misc
from os.path import splitext
sys.path.insert(0, '../../shared')
from base_input_utils import ForkJoiner, frameid_from_filename

BASE_FILE_NAME = sys.argv[1]
LABELS_FILE_VAL =  BASE_FILE_NAME + '-val.txt' 
GAZE_POS_ASC_FILE = BASE_FILE_NAME + '.asc'
PREDICT_FILE_VAL = BASE_FILE_NAME + '-pureflow'
RESIZE_SHAPE = (84,84,1)
heatmap_shape = 84
num_thread = 6

t1 = time.time()
print "Reading optical flow images..."
val_fid = []
png_files = []
with open(LABELS_FILE_VAL, 'r') as f:
    for line in f:
        line=line.strip()
        if line.startswith("#") or line == "": 
            continue # skip comments or empty lines
        fname, lbl, x, y, w = line.split(' ')
        file_name = splitext(fname)[0];
        if file_name[-2] == '_' and file_name[-1] == '1': # skip the first frame, because they don't have optical flow
            continue
        else:
            png_files.append(fname)
            val_fid.append(frameid_from_filename(fname))
       
N = len(png_files)
val_predict = np.empty((N,RESIZE_SHAPE[0],RESIZE_SHAPE[1],1), dtype=np.float32)

def read_thread(PID):
    d = os.path.dirname(LABELS_FILE_VAL)
    for i in range(PID, N, num_thread):
        img = misc.imread(os.path.join(d+'/optical_flow', png_files[i]))
        SUM = img.sum()
        img = img.astype(np.float32) / SUM # normalize the bottom up saliency map to a probability distribution
        val_predict[i,:,:,0] = img

o=ForkJoiner(num_thread=num_thread, target=read_thread)
o.join()
print "Done. Time spent to read optical flow images: %.1fs" % (time.time()-t1)


t2 = time.time()
print "Writing predicted results into the npz file..."
np.savez_compressed(PREDICT_FILE_VAL, fid=val_fid, heatmap=val_predict)
print "Done. Time spent to write npz file: %.1fs" % (time.time()-t2)
print "Outputs are:"
print " %s" % PREDICT_FILE_VAL+'.npz'


