#!/bin/bash

xhost +local: >/dev/null/ 2>&1

if docker ps -a --format '{{.Names}}' | grep -q '^yolov8-dev$'; then
  docker start yolov8-dev >/dev/null
else
  docker run -it --name yolov8-dev \
    --gpus all \
    --network host \
    --privileged \
    --device /dev/video4 \
    -e DISPLAY=$DISPLAY \ 
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v $HOME/ai-duck/duck_tracking:/workspace \
    yolov8-gui:jetson_final bash
   exit 0
fi

docker exec -it yolov8-dev bash -lc "cd /workspace && python3 yolo_live.py --cam 4 --conf 0.40 --classes 0"
