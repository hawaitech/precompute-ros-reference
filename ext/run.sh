#!/bin/bash

SRC_PATH=$1
DOC_PATH=$2
GRAPH_STYLE=$3

mkdir -p /tmp/docs/.venv
python3 -m venv /tmp/docs/.venv --system-site-packages
/tmp/docs/.venv/bin/python3 -m pip install ros2-graph
source /opt/ros/jazzy/setup.bash
source /workspace/install/setup.bash
source /tmp/docs/.venv/bin/activate
python3 $SRC_PATH/tmp/precompute-ros-reference/src/analyze_ros_packages.py \
    --src-path $SRC_PATH \
    --doc-path $DOC_PATH \
    --graph-style $GRAPH_STYLE