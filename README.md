<div align="center">
  <a href="https://www.youtube.com/watch?v=x2lotmG0Ts4"><img src="https://img.youtube.com/vi/x2lotmG0Ts4/0.jpg" alt="IVOS-Demo"></a>
</div>

# USAGE

## Download Video Sequences

Download from [Google Drive link](https://drive.google.com/file/d/1j_BYZm8G7689nEKd4GGxNtcv4WpLxzUk/view?usp=sharing) and unzip it

## Docker Image

### Create Docker container
```
xhost local:root

export $SEQUENCES=<absolute path of sequences>

docker run \
	-v $SEQUENCES:/mnt/sequences \
	-v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=unix$DISPLAY \
	--gpus=all -u qtuser -it \
	qcuong98/ivos-demo
```

### In the container
```
# export QT_DEBUG_PLUGINS=1 (for debugging)

python gui.py \
	[--gpus <gpu_ids for fbrs and stm>] \
	[--mem <mem_size>] \
	[--config <json_dir>] \
	--seq /mnt/sequences/<name-sequence>

# example: python gui.py --gpus 0 --mem 5 --seq /mnt/sequences/india
```

#### An example of config file objects:
*File **objects.json** describes that there are 3 object instances in the video sequence. Name of objects with id from 1 to 3 are **woman_1**, **woman_2**, and **woman_3**, respectively.*
```json
{
	"objects": [
		"woman_1",
		"woman_2",
		"woman_3",
	]
}
```
#### If json config is not specified, the default number of objecs is 5, and name of objects will be **object_1**, **object_2**, etc.

# CREDIT

A part of this repository is used for DAVIS Challenge 2020 Interactive

PyQt layout is modified from [Seoung Wug Oh's repository](https://github.com/seoungwugoh/ivs-demo)
