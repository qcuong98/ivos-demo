<div align="center">
  <a href="https://www.youtube.com/watch?v=x2lotmG0Ts4"><img src="https://img.youtube.com/vi/x2lotmG0Ts4/0.jpg" alt="IVOS-Demo"></a>
</div>

# USAGE

## Docker Image

Create Docker container
```
xhost local:root

export $SEQUENCES=<path of sequences>

docker run \
	-v $SEQUENCES:/mnt/sequences \
	-v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=unix$DISPLAY \
	--gpus=all -u qtuser -it \
	qcuong98/ivos-demo
```

In the container
```
# export QT_DEBUG_PLUGINS=1 (for debugging)

python gui.py --gpus <gpu_ids for fbrs and stm> --mem <mem_size> --seq /mnt/sequences/<name-sequence>

# example: python gui.py --gpus 0 --mem 5 --seq /mnt/sequences/parkour
```

# CREDIT

A part of this repository is used for DAVIS Challenge 2020 Interactive

PyQt layout is modified from [Seoung Wug Oh's repository](https://github.com/seoungwugoh/ivs-demo)
