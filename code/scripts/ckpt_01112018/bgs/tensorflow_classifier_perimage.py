#import matplotlib
#import matplotlib.pyplot as plt

import cv2
print("CV2 version: "+cv2.__version__)
import numpy as np

frame = cv2.imread("/home/junchenj/workspace/scripts/frames/out-000001.jpg")
print frame.shape


import os
import tensorflow as tf
try:
    import urllib2 as urllib
except ImportError:
    import urllib.request as urllib

from datasets import imagenet
from nets import inception
from nets import resnet_v1
from nets import vgg
from preprocessing import vgg_preprocessing

from tensorflow.contrib import slim

from datasets import dataset_utils

import sys, getopt, os
import ntpath
import time

EXTRACTION_LOG = ""
IMAGES_FOLDER = ""
OUTPUT_FILE = ""
MODEL = ""

opts, args = getopt.getopt(sys.argv[1:],"e:i:o:m:")
for o, a in opts:
    if o == '-e':
        EXTRACTION_LOG = a
    elif o == '-i':
        IMAGES_FOLDER = a
    elif o == '-o':
        OUTPUT_FILE = a
    elif o == '-m':
        MODEL = a
    else:
        print("Usage: %s -e extraction -i images -o output -m model" % sys.argv[0])
        sys.exit()
if (not EXTRACTION_LOG):
    print("Missing arguments -e")
    sys.exit()
if (not IMAGES_FOLDER):
    print("Missing arguments -i")
    sys.exit()
if (not OUTPUT_FILE):
    print("Missing arguments -o")
    sys.exit()
if (not MODEL):
    print("Missing arguments -m")
    sys.exit()

print "***********************************"
print "Extraction:\t"+EXTRACTION_LOG
print "Images path:\t"+IMAGES_FOLDER
print "Output file:\t"+OUTPUT_FILE
print "Model name:\t"+MODEL
print "***********************************"

model_to_url = {'inception_v1': 'inception_v1_2016_08_28', \
                'inception_v2': 'inception_v2_2016_08_28', \
                'inception_v3': 'inception_v3_2016_08_28', \
                'inception_v4': 'inception_v4_2016_09_09', \
                'resnet_v1_50': 'resnet_v1_50_2016_08_28', \
                'resnet_v1_101': 'resnet_v1_101_2016_08_28', \
                'resnet_v1_152': 'resnet_v1_152_2016_08_28', \
                'vgg_16': 'vgg_16_2016_08_28'}
model_to_image_size = {'inception_v1': inception.inception_v1.default_image_size, \
                       'inception_v2': inception.inception_v2.default_image_size, \
                       'inception_v3': inception.inception_v3.default_image_size, \
                       'inception_v4': inception.inception_v4.default_image_size, \
                       'resnet_v1_50': resnet_v1.resnet_v1_50.default_image_size, \
                       'resnet_v1_101': resnet_v1.resnet_v1_101.default_image_size, \
                       'resnet_v1_152': resnet_v1.resnet_v1_152.default_image_size, \
                       'vgg_16': vgg.vgg_16.default_image_size}
model_to_batch_size = {'inception_v1': 400, \
                       'inception_v2': 400, \
                       'inception_v3': 400, \
                       'inception_v4': 400, \
                       'resnet_v1_50': 400, \
                       'resnet_v1_101': 400, \
                       'resnet_v1_152': 400, \
                       'vgg_16': 100}


def preprocess_for_inception(image, height, width,
                        central_fraction=0.875, scope=None):
  with tf.name_scope(scope, 'eval_image', [image, height, width]):
    if image.dtype != tf.float32:
      image = tf.image.convert_image_dtype(image, dtype=tf.float32)
    # Crop the central region of the image with an area containing 87.5% of
    # the original image.
    if central_fraction:
      image = tf.image.central_crop(image, central_fraction=central_fraction)

    if height and width:
      # Resize the image to the specified height and width.
      image = tf.expand_dims(image, 0)
      image = tf.image.resize_bilinear(image, [height, width],
                                       align_corners=False)
      image = tf.squeeze(image, [0])
    image = tf.subtract(image, 0.5)
    image = tf.multiply(image, 2.0)
    return image

def batch_prediction(image_id_to_path, model, sess):
    print "batch processing: "+str(len(image_id_to_path))
    image_id_to_predictions = {}
    image_ids = []
    count = 0
    start_time_1 = time.time()
    for image_id,path in image_id_to_path.iteritems():
        image_string = open(path, 'rb').read()
        image = tf.image.decode_jpeg(image_string, channels=3)
        if model == 'inception_v1' or model == 'inception_v2' or model == 'inception_v3' or model == 'inception_v4':
            processed_image = preprocess_for_inception(image, image_size, image_size, central_fraction=1.0)
        elif model == 'vgg_16' or model == 'resnet_v1_50' or model == 'resnet_v1_101' or model == 'resnet_v1_152':
            processed_image = vgg_preprocessing.preprocess_image(image, image_size, image_size, is_training=False)
        start_time = time.time()
        #print processed_image.shape
        #np_val = sess.run(processed_image)
        #print np_val.shape
        #processed_image = tf.convert_to_tensor(np_val)
        #print processed_image.shape
        #print "conversion: "+str(time.time()-start_time)+" seconds"
        if count == 0:
            processed_images = tf.expand_dims(processed_image, 0)
        else:
            local_matrix  = tf.expand_dims(processed_image, 0)
            processed_images = tf.concat([processed_images, local_matrix], 0)
        image_ids.append(image_id)
        count = count+1
    print "Preparation: "+str(time.time()-start_time_1)+" seconds"
    start_time = time.time()
    if model == 'inception_v1':
        logits, _ = inception.inception_v1(processed_images, num_classes=1001, is_training=False)
        init_fn = slim.assign_from_checkpoint_fn(
            os.path.join(checkpoints_dir, 'inception_v1.ckpt'),
            slim.get_model_variables('InceptionV1'))
    elif model == 'inception_v2':
        logits, _ = inception.inception_v2(processed_images, num_classes=1001, is_training=False)
        init_fn = slim.assign_from_checkpoint_fn(
            os.path.join(checkpoints_dir, 'inception_v2.ckpt'),
            slim.get_model_variables('InceptionV2'))
    elif model == 'inception_v3':
        logits, _ = inception.inception_v3(processed_images, num_classes=1001, is_training=False)
        init_fn = slim.assign_from_checkpoint_fn(
            os.path.join(checkpoints_dir, 'inception_v3.ckpt'),
            slim.get_model_variables('InceptionV3'))
    elif model == 'inception_v4':
        logits, _ = inception.inception_v4(processed_images, num_classes=1001, is_training=False)
        init_fn = slim.assign_from_checkpoint_fn(
            os.path.join(checkpoints_dir, 'inception_v4.ckpt'),
            slim.get_model_variables('InceptionV4'))
    elif model == 'resnet_v1_50':
        logits, _ = resnet_v1.resnet_v1_50(processed_images, num_classes=1000, is_training=False)
        init_fn = slim.assign_from_checkpoint_fn(
            os.path.join(checkpoints_dir, 'resnet_v1_50.ckpt'),
            slim.get_model_variables('resnet_v1_50'))
    elif model == 'resnet_v1_101':
        logits, _ = resnet_v1.resnet_v1_101(processed_images, num_classes=1000, is_training=False)
        init_fn = slim.assign_from_checkpoint_fn(
            os.path.join(checkpoints_dir, 'resnet_v1_101.ckpt'),
            slim.get_model_variables('resnet_v1_101'))
    elif model == 'resnet_v1_152':
        logits, _ = resnet_v1.resnet_v1_152(processed_images, num_classes=1000, is_training=False)
        init_fn = slim.assign_from_checkpoint_fn(
            os.path.join(checkpoints_dir, 'resnet_v1_152.ckpt'),
            slim.get_model_variables('resnet_v1_152'))
    elif model == 'vgg_16':
        logits, _ = vgg.vgg_16(processed_images, num_classes=1000, is_training=False)
        init_fn = slim.assign_from_checkpoint_fn(
            os.path.join(checkpoints_dir, 'vgg_16.ckpt'),
            slim.get_model_variables('vgg_16'))
    print "Prediction2.1: "+str(time.time()-start_time)+" seconds"
    start_time = time.time()
    init_fn(sess)
    print "Prediction2.2: "+str(time.time()-start_time)+" seconds"
    probabilities = tf.nn.softmax(logits)
    print "Prediction1: "+str(time.time()-start_time)+" seconds"

    start_time = time.time()
    np_image, probabilities = sess.run([image, probabilities])
    runtime = time.time()-start_time
    print "Prediction: "+str(runtime)+" seconds"
    for k in range(len(image_ids)):
        image_id = image_ids[k]
        predictions = []
        prob = probabilities[k, 0:]
        sorted_inds = [i[0] for i in sorted(enumerate(-prob), key=lambda x:x[1])]
        for i in range(5):
            index = sorted_inds[i]
            if model == 'inception_v1' or model == 'inception_v2' or model == 'inception_v3' or model == 'inception_v4':
                name = names[index]
            elif model == 'vgg_16' or model == 'resnet_v1_50' or model == 'resnet_v1_101' or model == 'resnet_v1_152':
                name = names[index+1]
            pr = prob[index]
            pair = (name, pr)
            predictions.append(pair)
        image_id_to_predictions[image_id] = predictions
    return image_id_to_predictions, runtime, sess


def process_super_batch(frame_ids, frame_id_to_path, \
                        frame_id_to_image_ids, image_id_to_path, \
                        image_id_to_coordinates, output, model, sess):
    image_id_to_predictions, runtime, sess = batch_prediction(image_id_to_path, model, sess)
    for m in range(len(frame_ids)):
        frame_id = frame_ids[m]
        frame_path = frame_id_to_path[frame_id]
        output.write("FrameID="+frame_id+"\n")
        runtime_per_frame = float(runtime)/float(len(image_id_to_path))\
                            *float(len(frame_id_to_image_ids[frame_id]))
        output.write(frame_path+": "+str(runtime_per_frame)+" seconds"+"\n")
        for n in range(len(frame_id_to_image_ids[frame_id])):
            image_id = frame_id_to_image_ids[frame_id][n]
            coordinates = image_id_to_coordinates[image_id]
            predictions = image_id_to_predictions[image_id]
            name = predictions[0][0]
            prob = float(predictions[0][1])
            #if prob < 0.3:
            #    continue
            output.write(image_id_to_path[image_id]+"\n")
            output.write(name+": "+"{0:.2f}".format(prob*100)+"%\t"+coordinates+"\n")
    

def process(lines, split_index_list, output_file, model, batch_size):
    frame_ids = []
    frame_id_to_path = {}
    frame_id_to_image_ids = {}
    image_id_to_path = {}
    image_id_to_coordinates = {}
    for i in range(len(split_index_list)-1):
        frame_path = lines[split_index_list[i]].rstrip()
        frame_id = ntpath.basename(frame_path)
        frame_ids.append(frame_id)
        frame_id_to_path[frame_id] = frame_path
        num_images = split_index_list[i+1]-split_index_list[i]-1
        image_ids = []
        for j in range(num_images):
            line = lines[split_index_list[i]+j+1]
            fields = line.rstrip().split("\t")
            image_path = fields[0]
            image_id = ntpath.basename(image_path)
            coordinates = fields[1]+"\t"+fields[2]+"\t"+fields[3]+"\t"+fields[4]
            image_path = os.path.join(IMAGES_FOLDER,image_id)
            image_id_to_path[image_id] = image_path
            image_id_to_coordinates[image_id] = coordinates
            image_ids.append(image_id)
        frame_id_to_image_ids[frame_id] = image_ids
        if (len(image_id_to_path) < batch_size and i+1 < len(split_index_list)-1) or len(frame_ids) == 0:
            continue
        print frame_id
        output = open(output_file, "a")
        if model == 'inception_v1': 
            tf.Graph().as_default()
            with tf.Session(graph=tf.Graph()) as sess:
                with slim.arg_scope(inception.inception_v1_arg_scope()):
                    process_super_batch(frame_ids, frame_id_to_path, frame_id_to_image_ids, \
                                        image_id_to_path, image_id_to_coordinates, output, model, sess)
        if model == 'inception_v2':
            tf.Graph().as_default()
            with tf.Session(graph=tf.Graph()) as sess:
                with slim.arg_scope(inception.inception_v2_arg_scope()):
                    process_super_batch(frame_ids, frame_id_to_path, frame_id_to_image_ids, \
                                        image_id_to_path, image_id_to_coordinates, output, model, sess)
        if model == 'inception_v3':
            tf.Graph().as_default()
            with tf.Session(graph=tf.Graph()) as sess:
                with slim.arg_scope(inception.inception_v3_arg_scope()):
                    process_super_batch(frame_ids, frame_id_to_path, frame_id_to_image_ids, \
                                        image_id_to_path, image_id_to_coordinates, output, model, sess)
        if model == 'inception_v4':
            tf.Graph().as_default()
            with tf.Session(graph=tf.Graph()) as sess:
                with slim.arg_scope(inception.inception_v4_arg_scope()):
                    process_super_batch(frame_ids, frame_id_to_path, frame_id_to_image_ids, \
                                        image_id_to_path, image_id_to_coordinates, output, model, sess)
        if model == 'resnet_v1_50':
            tf.Graph().as_default()
            with tf.Session(graph=tf.Graph()) as sess:
                with slim.arg_scope(resnet_v1.resnet_arg_scope()):
                    process_super_batch(frame_ids, frame_id_to_path, frame_id_to_image_ids, \
                                        image_id_to_path, image_id_to_coordinates, output, model, sess)
        if model == 'resnet_v1_101':
            tf.Graph().as_default()
            with tf.Session(graph=tf.Graph()) as sess:
                with slim.arg_scope(resnet_v1.resnet_arg_scope()):
                    process_super_batch(frame_ids, frame_id_to_path, frame_id_to_image_ids, \
                                        image_id_to_path, image_id_to_coordinates, output, model, sess)
        if model == 'resnet_v1_152':
            tf.Graph().as_default()
            with tf.Session(graph=tf.Graph()) as sess:
                with slim.arg_scope(resnet_v1.resnet_arg_scope()):
                    process_super_batch(frame_ids, frame_id_to_path, frame_id_to_image_ids, \
                                        image_id_to_path, image_id_to_coordinates, output, model, sess)
        elif model == 'vgg_16':
            tf.Graph().as_default()
            with tf.Session(graph=tf.Graph()) as sess:
                with slim.arg_scope(vgg.vgg_arg_scope()):
                    process_super_batch(frame_ids, frame_id_to_path, frame_id_to_image_ids, \
                                        image_id_to_path, image_id_to_coordinates, output, model, sess)
        output.close()
        frame_ids = []
        frame_id_to_path = {}
        frame_id_to_image_ids = {}
        image_id_to_path = {}
        image_id_to_coordinates = {}
                
            

log = open(EXTRACTION_LOG, "r")
split_index_list = []
lines = []
count = 0
for line in log:
    if len(line.split("\t")) == 1:
        split_index_list.append(count)
    lines.append(line)
    count += 1
split_index_list.append(count)

output = open(OUTPUT_FILE, "w")
output.write("")
output.close()

url = "http://download.tensorflow.org/models/"+model_to_url[MODEL]+".tar.gz"
checkpoints_dir = '/tmp/checkpoints'

if not tf.gfile.Exists(checkpoints_dir):
    tf.gfile.MakeDirs(checkpoints_dir)

dataset_utils.download_and_uncompress_tarball(url, checkpoints_dir)
image_size = model_to_image_size[MODEL]
batch_size = model_to_batch_size[MODEL]
names = imagenet.create_readable_names_for_imagenet_labels()

global_start_time = time.time()
process(lines, split_index_list, OUTPUT_FILE, MODEL, batch_size)
print "Prediction: "+str(time.time()-global_start_time)+" seconds"

 
