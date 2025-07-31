#!/bin/bash

DEST=$1

echo Preparing copy to $DEST/tmp/precompute-ros-reference.
echo Directory contains :
ls $DEST/tmp/precompute-ros-reference

rm -rf $DEST/tmp/precompute-ros-reference
mkdir -p $DEST/tmp/precompute-ros-reference
cp -r /ext/. $DEST/tmp/precompute-ros-reference

echo Finished copy to $DEST/tmp/precompute-ros-reference.
echo Directory contains :
ls $DEST/tmp/precompute-ros-reference
