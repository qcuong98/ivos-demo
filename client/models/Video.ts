type RVFCMetadata = {
  mediaTime: number;
};
type RVFCCallBack = (_: any, metadata: RVFCMetadata) => void;
interface RVFCVideoElement extends HTMLVideoElement {
  requestVideoFrameCallback?: (cb: RVFCCallBack) => void;
}

class Video {
  video: RVFCVideoElement;
  fps: number;
  _rvfc_currentFrameId: number = 0;

  constructor(elementId: string, fps: number) {
    let tmp = document.getElementById(elementId);
    if (!tmp) {
      throw new Error(`No HTML element with ID = ${elementId} exists`);
    }
    this.video = tmp as RVFCVideoElement;
    this.fps = fps;

    if (this.video.requestVideoFrameCallback) {
      this.initialiseRVFC();
    }
  }

  initialiseRVFC() {
    let updateCurrentFrameId = (_: any, metadata: RVFCMetadata) => {
      let count = metadata.mediaTime * this.fps;
      this._rvfc_currentFrameId = Math.round(count);
      this.video.requestVideoFrameCallback!(updateCurrentFrameId);
    };
    this.video.requestVideoFrameCallback!(updateCurrentFrameId);
  }

  getCurrentFrameId() {
    let ans = this.video.requestVideoFrameCallback
      ? this._rvfc_currentFrameId
      : Math.round(this.video.currentTime * this.fps);
    ans = Math.max(0, ans);
    ans = Math.min(ans, this.video.duration * this.fps);
    return ans;
  }

  addEventListener<K extends keyof HTMLMediaElementEventMap>(
    type: K,
    listener: (this: HTMLVideoElement, e: HTMLMediaElementEventMap[K]) => any
  ) {
    this.video.addEventListener(type, listener);
  }

  removeEventListener<K extends keyof HTMLMediaElementEventMap>(
    type: K,
    listener: (this: HTMLVideoElement, e: HTMLMediaElementEventMap[K]) => any
  ) {
    this.video.removeEventListener(type, listener);
  }

  get isPlaying() {
    return !this.video.paused;
  }

  resume() {
    this.video.play();
  }
}

export default Video;
