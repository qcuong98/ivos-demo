# USAGE

## Docker Image

Create Docker Container
```
xhost local:root

export $SEQUENCES=<path of sequences>

docker run \
	-v $SEQUENCES:/mnt/sequences \
	-v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=unix$DISPLAY \
	--gpus=all -u qtuser -it \
	qcuong98/ivos-demo
```

In the containeer

```
# export QT_DEBUG_PLUGINS=1 (for debugging)

python gui.py --gpus <gpu_ids for fbrs and stm> --mem <mem_size> --seq /mnt/sequences/<name-sequence>

# example: python gui.py --gpus 0 --mem 5 --seq /mnt/sequences/parkour
```

# Credit

A part of this repository is used for DAVIS Challenge 2020 Interactive

PyQt layout is modified from [Seoung Wug Oh's repository](https://github.com/seoungwugoh/ivs-demo)
