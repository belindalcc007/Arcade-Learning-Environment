import tensorflow as tf, numpy as np, keras as K, sys
import keras.layers as L
from keras.models import Model, Sequential # keras/engine/training.py
from IPython import embed
import ipdb
import json
import sys

print("Usage: ipython main.py [PredictMode?]")
print("Usage Predict Mode: ipython main.py 1 parameters Model.hdf5")
print("Usage Training Mode: ipython main.py 0 parameters")
#TRAIN_DATASET = ['40_RZ_4983433_May-16-20-19-52']
#VAL_DATASET = ['45_RZ_5134712_May-18-14-14-00']
#TRAIN_DATASET = ['42_RZ_4988291_May-16-21-33-46']
#VAL_DATASET = ['44_RZ_5131746_May-18-13-25-32']
TRAIN_DATASET = ['36_RZ_4882422_May-15-16-08-32','38_RZ_4886422_May-15-17-15-33','39_RZ_4981421_May-16-19-40-17','43_RZ_5129700_May-18-12-52-16']
#TRAIN_DATASET = ['36_RZ_4882422_May-15-16-08-32']
VAL_DATASET = ['37_RZ_4883794_May-15-16-37-01']
#TRAIN_DATASET = ['47_KM_1535284_Jul-31-16-10-56']
#VAL_DATASET = ['48_KM_1537673_Jul-31-16-51-20']

#BASE_FILE_NAME = "/scratch/cluster/zharucs/dataset_gaze/cat{40_RZ}tr_{45_RZ}val"
#BASE_FILE_NAME = "/scratch/cluster/zharucs/dataset_gaze/cat{42_RZ}tr_{44_RZ}val"
#BASE_FILE_NAME = "/scratch/cluster/zharucs/dataset_gaze/cat{36_RZ}tr_{37_RZ}val"
BASE_FILE_NAME = "/scratch/cluster/zharucs/dataset_gaze/cat{36_38_39_43_RZ}tr_{37_RZ}val"
#BASE_FILE_NAME = "/scratch/cluster/zharucs/dataset_gaze/cat{36_37_38_39_43_RZ}tr_{47_48_KM}val"
#BASE_FILE_NAME = "/scratch/cluster/zharucs/dataset_gaze/cat{47_KM}tr_{48_KM}val"

LABELS_FILE_TRAIN = BASE_FILE_NAME + '-train.txt' 
LABELS_FILE_VAL =  BASE_FILE_NAME + '-val.txt' 
GAZE_POS_ASC_FILE = BASE_FILE_NAME + '.asc'
PREDICT_FILE_TRAIN = BASE_FILE_NAME + '-train-result'
PREDICT_FILE_VAL = BASE_FILE_NAME + '-val-result'
SHAPE = (84,84,1) # height * width * channel This cannot read from file and needs to be provided here
BATCH_SIZE = 50
heatmap_shape = 84
#lr = float(sys.argv[3])
num_epoch = 50
MODEL_DIR = 'Seaquest_36-43_37'
#MODEL_DIR = 'Breakout_42_44'
#MODEL_DIR = 'Seaquest_47_48'
#MODEL_DIR = 'Pacman_40_45'
#MODEL_DIR = 'Seaquest_36_37'
resume_model = False
predict_mode = int(sys.argv[1]) 
dropout = float(sys.argv[2])


if not predict_mode: # if train
    import input_utils as IU, misc_utils as MU
    expr = MU.BMU.ExprCreaterAndResumer(MODEL_DIR, postfix="salient_reshape_dp" + str(dropout))
    expr.redirect_output_to_logfile_if_not_on("eldar-11")
else:
    import all_py_files_snapshot.input_utils as IU, all_py_files_snapshot.misc_utils as MU

MU.BMU.save_GPU_mem_keras()
MU.keras_model_serialization_bug_fix()

if resume_model:
    model = expr.load_weight_and_training_config_and_state()
    expr.printdebug("Checkpoint found. Resuming model at %s" % expr.dir_lasttime)
else:
    ###############################
    # Architecture of the network #
    ###############################

    inputs=L.Input(shape=SHAPE)
    x=inputs # inputs is used by the line "Model(inputs, ... )" below
    x=L.Conv2D(32, (8,8), strides=4, padding='same')(x)
    x=L.BatchNormalization()(x)
    x=L.Activation('relu')(x)
    x=L.Dropout(dropout)(x)
    
    x=L.Conv2D(64, (4,4), strides=2, padding='same')(x)
    x=L.BatchNormalization()(x)
    x=L.Activation('relu')(x)
    x=L.Dropout(dropout)(x)
    
    x=L.Conv2D(64, (3,3), strides=1, padding='same')(x)
    x=L.BatchNormalization()(x)
    x=L.Activation('relu')(x)
    x=L.Dropout(dropout)(x)

    x = L.Flatten()(x)
    x = L.Dense(512, activation = "relu")(x)
    x = L.Dropout(dropout)(x)

    x = L.Dense(7056, activation = "softmax")(x)
    logits =  L.Reshape((84, 84, -1), name = "logits")(x)

    model=Model(inputs=inputs, outputs=logits)

    opt=K.optimizers.Adadelta(lr=1.0, rho=0.95, epsilon=1e-08, decay=0.0)
    # opt=K.optimizers.Adam(lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=1e-08)
    # opt=K.optimizers.SGD(lr=lr, momentum=0.99, decay=1e-6, nesterov=True)
    
    model.compile(loss=MU.my_kld, optimizer=opt, metrics=[MU.computeNSS])
    
d=IU.DatasetWithHeatmap(LABELS_FILE_TRAIN, LABELS_FILE_VAL, SHAPE, heatmap_shape, GAZE_POS_ASC_FILE)

if not predict_mode: # if train
    expr.dump_src_code_and_model_def(sys.argv[0], model)

    model.fit(d.train_imgs, d.train_GHmap, BATCH_SIZE, epochs=num_epoch,
        validation_data=(d.val_imgs, d.val_GHmap),
        shuffle=True,verbose=2,
        callbacks=[K.callbacks.TensorBoard(log_dir=expr.dir),
            K.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, min_lr = 0.00001),
            MU.BMU.PrintLrCallback()])
    #model.fit(d.train_imgs, d.train_gaze, BATCH_SIZE, epochs=num_epoch,
    #    validation_data=(d.val_imgs, d.val_gaze),
    #    shuffle=True,verbose=2,
    #    callbacks=[K.callbacks.TensorBoard(log_dir=expr.dir),  
    #        MU.BMU.PrintLrCallback()])

    expr.save_weight_and_training_config_state(model)

    score = model.evaluate(d.val_imgs, d.val_GHmap, BATCH_SIZE, 0)
    expr.printdebug("eval score:" + str(score))

elif predict_mode: # if predict
    model.load_weights(sys.argv[3])

    print "Evaluating model..."
    train_score = model.evaluate(d.train_imgs, d.train_GHmap, BATCH_SIZE, 0)
    val_score = model.evaluate(d.val_imgs, d.val_GHmap, BATCH_SIZE, 0)
    print "Train loss is:  " , train_score
    print "Val loss is: " , val_score

    print "Predicting results..."
    train_pred = model.predict(d.train_imgs, BATCH_SIZE) # [1] for prob
    val_pred = model.predict(d.val_imgs, BATCH_SIZE)
    print "Predicted."

    print "Converting predicted results into png files and save..."
    IU.save_heatmap_png_files(d.train_fid, train_pred, TRAIN_DATASET, 'saliency/')
    IU.save_heatmap_png_files(d.val_fid, val_pred, VAL_DATASET, 'saliency/')
    print "Done."
