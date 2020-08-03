import Player, { VideoJsPlayer } from "video.js";

type RVFCMetadata = {
  mediaTime: number;
};
type RVFCCallBack = (_: any, metadata: RVFCMetadata) => void;
interface RVFCVideoElement extends HTMLVideoElement {
  requestVideoFrameCallback?: (cb: RVFCCallBack) => void;
}

class Video {
  video: VideoJsPlayer;
  fps: number;
  _elementId: string;
  _rvfc_currentFrameId: number = 0;
  _videoElement: RVFCVideoElement | null = null;

  constructor(elementId: string, fps: number) {
    this.video = Player(elementId);
    this.fps = fps;
    this._elementId = elementId;

    // @ts-ignore
    this.video.controlBar.pictureInPictureToggle?.dispose();
    // @ts-ignore
    this.video.controlBar.fullscreenToggle?.dispose();

    if (this.supportRVFC()) {
      this.initialiseRVFC();
    }
  }

  supportRVFC() {
    let videoJsElement = document.getElementById(this._elementId);
    if (!videoJsElement) {
      return false;
    }
    let videoElement = videoJsElement.querySelector("video");
    if (!videoElement) {
      return false;
    }
    this._videoElement = videoElement;
    let rvfcVideoElement = videoElement as RVFCVideoElement;
    if (rvfcVideoElement.requestVideoFrameCallback) {
      return true;
    }
    return false;
  }

  initialiseRVFC() {
    let updateCurrentFrameId = (_: any, metadata: RVFCMetadata) => {
      let count = metadata.mediaTime * this.fps;
      this._rvfc_currentFrameId = Math.round(count);
      this._videoElement?.requestVideoFrameCallback!(updateCurrentFrameId);
    };
    this._videoElement?.requestVideoFrameCallback!(updateCurrentFrameId);
  }

  getCurrentFrameId() {
    let ans = this._videoElement?.requestVideoFrameCallback
      ? this._rvfc_currentFrameId
      : Math.round(this.video.currentTime() * this.fps);
    ans = Math.max(0, ans);
    ans = Math.min(ans, this.video.duration() * this.fps);
    return ans;
  }

  addEventListener<K extends keyof HTMLMediaElementEventMap>(
    type: K,
    listener: (this: HTMLVideoElement, e: HTMLMediaElementEventMap[K]) => any
  ) {
    this._videoElement?.addEventListener(type, listener);
  }

  removeEventListener<K extends keyof HTMLMediaElementEventMap>(
    type: K,
    listener: (this: HTMLVideoElement, e: HTMLMediaElementEventMap[K]) => any
  ) {
    this._videoElement?.removeEventListener(type, listener);
  }

  get isPlaying(): boolean {
    return !this.video.paused();
  }

  resume() {
    this._videoElement?.play();
  }
}

export default Video;
