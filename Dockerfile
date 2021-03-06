FROM nvidia/cuda:10.0-devel-ubuntu18.04
RUN apt-get update && apt-get install -y wget libgl1-mesa-glx libgtk2.0-dev \
    libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 \
    libxcb-render-util0 libxcb-render0 libxcb-shm0 libxcb-xfixes0 libxcb-sync0-dev \
    libxcb-shape0 libxcb-xfixes0 libxcb-xkb1 \
    libxkbcommon-x11-0 libxkbcommon0

ENV USER qtuser
ENV HOME /home/$USER

# Add user
RUN adduser --quiet --disabled-password qtuser

# Install Miniconda
ENV CONDA_DIR $HOME/miniconda3
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh \
    && chmod +x ~/miniconda.sh \
    && ~/miniconda.sh -b -p $CONDA_DIR \
    && rm ~/miniconda.sh
ENV PATH=$CONDA_DIR/bin:${PATH}


RUN conda create -n env python=3.6
RUN echo "source activate env" > ~/.bashrc

SHELL ["/bin/bash", "-c"]

# Install DL libraries
RUN source activate env && \
    conda config --add channels pytorch
RUN source activate env && \
    conda config --add channels conda-forge
RUN source activate env && conda install -y \
    pytorch=1.4.0 torchvision cudatoolkit=10.0 tqdm pyqt==5.9.2
RUN source activate env && pip install -q Cython==0.29.21
RUN source activate env && pip install -q tensorboard==2.2.2 easydict==1.9 PyYAML==5.3.1 davisinteractive==1.0.4

# Install Web libraries
RUN apt install -y curl
RUN curl -sL https://deb.nodesource.com/setup_10.x | bash
RUN apt install nodejs
RUN npm install --global yarn
RUN source activate env && pip install -q gunicorn==20.0.4 Flask==1.1.2

COPY . /app

RUN chown -R $USER $HOME/.npm
RUN chown -R $USER $HOME/.config
RUN chown -R $USER /app
USER $USER
WORKDIR /app
