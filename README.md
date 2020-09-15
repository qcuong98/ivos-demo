<div align="center">
  <a href="https://www.youtube.com/watch?v=h690-ziAOeU"><img src="https://img.youtube.com/vi/h690-ziAOeU/0.jpg" alt="Video Object Annotation Tool"></a>
</div>

# REQUIREMENTS
- Docker >= 19.03
- CUDA >= 10.0

# USAGE

## Prepare Videos

Prepare your videos or download from [here](https://drive.google.com/drive/folders/1qMKeQjGUvPwiIcOZEMUtB0n5clegyvN7?usp=sharing) 

## Run By Docker Image

### Create Docker container
```
xhost local:root

export VIDEOS=<absolute path of videos folder>
export EXPOSED_PORT=8000

docker run \
	-v $VIDEOS:/mnt/videos \
	-v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=unix$DISPLAY \
	-p $EXPOSED_PORT:8000 \
	--gpus=all -u qtuser -itd \
	qcuong98/ivos-demo

docker exec -it <container_id, output of docker run command> bash

```

### In the container
```
yarn install && yarn build
./server/run_api.sh

python gui.py \
	[--gpus <gpu_ids for fbrs and stm>] \
	[--mem <memory size>] \
	[--config <json directory>] \
	[--step <step frame>] \
	--video /mnt/videos/<video-name>.mp4

# example: python gui.py --gpus 0 --mem 5 --video /mnt/videos/india.mp4
```

Annotation results are shown in ```localhost:EXPORSED_PORT```

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
#### If json config is not specified, name of objects will be **object_1**, **object_2**, ..., **object_5**.

## Run by Source

### Download pretrained weights
- [f-BRS](https://drive.google.com/file/d/1gO27zyZuW2o48MbpBR8L4-90EPG3kaJE/view?usp=sharing): save in **segmentation/fbrs/weights/resnet50_dh128_lvis.pth**
- [STM](https://drive.google.com/file/d/1sgf2FhDN6XNf9AQPrD6mXLdUhnXH1t4r/view?usp=sharing): save in **propagation/STM/STM_weights.pth**

### Annotation Tool
```
python gui.py \
	[--gpus <gpu_ids for fbrs and stm>] \
	[--mem <memory size>] \
	[--config <json directory>] \
	[--step <step frame>] \
	--video <video-path>.mp4
```
### Semantic Video Website
```
yarn install && yarn build
./server/run_api.sh <port>
```

# CREDIT

A part of this repository is used for DAVIS Challenge 2020 Interactive Scenario

PyQt layout is modified from [Seoung Wug Oh's repository](https://github.com/seoungwugoh/ivs-demo)
