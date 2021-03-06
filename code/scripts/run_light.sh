video=$1

echo $video

FOLDER=$(pwd)
echo $FOLDER

ROOT=/home/junchenj/workspace/fast_newsize_result_${video}
rm -r $ROOT
mkdir $ROOT
echo $ROOT

FRAMES=${ROOT}/frames
rm -r ${FRAMES}
mkdir ${FRAMES}

ffmpeg -loglevel quiet -i ~/videos/${video}*.mp4 ${FRAMES}/out-%06d.jpg

cd /home/junchenj/workspace/scripts/tf/

DEFAULT_SIZE=400
DEFAULT_SAMPLING=0.033
DEFAULT_MODEL=faster_rcnn_resnet50

for x in faster_rcnn_nas faster_rcnn_resnet101 faster_rcnn_inception_v2 ssd_mobilenet_v1 faster_rcnn_inception_resnet rfcn_resnet101 faster_rcnn_resnet50 ssd_inception_v2 faster_rcnn_resnet50_lowproposals; do
    model=$x
    sampling=${DEFAULT_SAMPLING}
    size=${DEFAULT_SIZE}
    output=${ROOT}/Detections_Size_${size}_Sampling_${sampling}_Model_${model}.txt
    python cropping_test.py -t ~/workspace/tensorflow/models/ -i ${FRAMES} -o ${output} -m ${model} -r ${sampling} -s $size
    rm -rf ${model}*
done

for y in 0.33; do
    model=${DEFAULT_MODEL}
    sampling=$y
    size=${DEFAULT_SIZE}
    output=${ROOT}/Detections_Size_${size}_Sampling_${sampling}_Model_${model}.txt
    python cropping_test.py -t ~/workspace/tensorflow/models/ -i ${FRAMES} -o ${output} -m ${model} -r ${sampling} -s $size
    rm -rf ${model}*
done

for z in 1600 1200 800 400 200 ; do
    model=${DEFAULT_MODEL}
    sampling=${DEFAULT_SAMPLING}
    size=$z
    output=${ROOT}/Detections_Size_${size}_Sampling_${sampling}_Model_${model}.txt
    python cropping_test.py -t ~/workspace/tensorflow/models/ -i ${FRAMES} -o ${output} -m ${model} -r ${sampling} -s $size
    rm -rf ${model}*
done


cd $FOLDER

<< 'END'
cd /home/junchenj/workspace/scripts/bgs/

DEFAULT_MINAREA=0.001
DEFAULT_MODEL='resnet_v1_101'
DEFAULT_SAMPLING='0.033'

IMAGES=${ROOT}/images

for x in 0.0001; do
minarea=$x
python extraction.py -f ${FRAMES} -o ${IMAGES} -m ${minarea}
for y in nasnet_large resnet_v1_101 inception_v2 mobilenet_v1; do
    model=$y
    sampling=${DEFAULT_SAMPLING}
    output=${ROOT}/Classifications_MinArea_${minarea}_Sampling_${sampling}_Model_${model}.txt
    python tensorflow_classifier.py -e ${IMAGES}/log.txt -i ${IMAGES} -o ${output} -m ${model} -r ${sampling}
    rm -rf /tmp/checkpoints/*
done
done

END

rm -r ${FRAMES}
rm -r ${IMAGES}

cd $FOLDER
