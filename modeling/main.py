import tensorflow as tf, numpy as np, keras as K, sys
import keras.layers as L
from keras.models import Model, Sequential # keras/engine/training.py
from IPython import embed
import input_utils, misc_utils as MU
import ipdb

NUM_CLASSES=8
BASE_FILE_NAME = "/scratch/cluster/zhuode93/dataset/cat{36_FV}tr_{37_FV}val"
LABELS_FILE_TRAIN = BASE_FILE_NAME + '-train.txt' 
LABELS_FILE_VAL =  BASE_FILE_NAME + '-val.txt' 
GAZE_POS_ASC_FILE = BASE_FILE_NAME + '.asc'
k, stride = 1,1
SHAPE = (84,84,k) # height * width * channel This cannot read from file and needs to be provided here
BATCH_SIZE=100
num_epoch = 25
dropout = 0.25
MODEL_DIR = 'GazeExpr{36}tr_{37}val'
resume_model = False

MU.save_GPU_mem_keras()
MU.keras_model_serialization_bug_fix()

expr = MU.ExprCreaterAndResumer(MODEL_DIR,postfix="fov_CenterGaze_2x_k%ds%d" % (k, stride))
expr.redirect_output_to_logfile_if_not_on("eldar-11")

if resume_model:
    model = expr.load_weight_and_training_config_and_state()
    expr.printdebug("Checkpoint found. Resuming model at %s" % expr.dir_lasttime)
else:
    SHAPE_AFTER_CENTER_AT_GAZE_POS_PREPROCESSING = (SHAPE[0]*2,SHAPE[1]*2,SHAPE[2])
    inputs=L.Input(shape=SHAPE_AFTER_CENTER_AT_GAZE_POS_PREPROCESSING)
    x=inputs # inputs is used by the line "Model(inputs, ... )" below
    x=L.Conv2D(20, (8,8), strides=4, padding='same')(x)
    x=L.BatchNormalization()(x)
    x=L.Activation('relu')(x)
    x=L.Dropout(dropout)(x)
    
    x=L.Conv2D(40, (4,4), strides=2, padding='same')(x)
    x=L.BatchNormalization()(x)
    x=L.Activation('relu')(x)
    x=L.Dropout(dropout)(x)
    
    x=L.Conv2D(80, (3,3), strides=2, padding='same')(x)
    x=L.BatchNormalization()(x)
    x=L.Activation('relu')(x)
    x=L.Dropout(dropout)(x)
    x=L.Flatten()(x)
    
    x=L.Dense(256, activation='relu')(x)
    x=L.Dropout(dropout)(x)
    logits=L.Dense(NUM_CLASSES, name="logits")(x)
    prob=L.Activation('softmax', name="prob")(logits)
    model=Model(inputs=inputs, outputs=[logits, prob])

    opt=K.optimizers.Adadelta(lr=1.0, rho=0.95, epsilon=1e-08, decay=0.0)

    model.compile(loss={"prob":None, "logits": MU.loss_func},
                 optimizer=opt,metrics={"logits": MU.acc_})

expr.dump_src_code_and_model_def(sys.argv[0], model)

d=input_utils.DatasetCenteredAtLastGaze(LABELS_FILE_TRAIN, LABELS_FILE_VAL, SHAPE, GAZE_POS_ASC_FILE, K=k, stride=stride)
model.fit(d.train_imgs, d.train_lbl, BATCH_SIZE, epochs=num_epoch,
    validation_data=(d.val_imgs, d.val_lbl),
    shuffle=True,verbose=2,
    callbacks=[K.callbacks.TensorBoard(log_dir=expr.dir),
        K.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5,patience=3, min_lr=0.001),
        MU.PrintLrCallback()])

expr.save_weight_and_training_config_state(model)

score = model.evaluate(d.val_imgs, d.val_lbl, BATCH_SIZE, 0)
expr.printdebug("eval score:" + str(score))
