import { initialiseCanvasSize } from "./video-utils";
import Video from "./models/Video";
import Mask from "./models/Mask";

type MouseEventListener = (e: MouseEvent) => void;
type Metadata = {
  fps: number;
  objects: string[];
};

function fetchMetadata(): Promise<Metadata> {
  return fetch("/objects.json").then((res) => res.json());
}

window.onload = async function () {
  let { height, width } = await initialiseCanvasSize();
  let { objects: objectNameList, fps } = await fetchMetadata();
  let video = new Video("video", fps);

  let canvas = document.getElementById("main-canvas") as HTMLCanvasElement;
  let ctx = canvas.getContext("2d")!;
  let { x: offsetX, y: offsetY } = canvas.getBoundingClientRect();

  let mouseMoveListener: MouseEventListener | null = null;
  let mouseClickListener: MouseEventListener | null = null;

  function clearCanvas() {
    ctx.clearRect(0, 0, width, height);
  }

  function cleanup() {
    canvas.style.zIndex = "-1";
    if (mouseMoveListener) {
      window.removeEventListener("mousemove", mouseMoveListener);
    }
    if (mouseClickListener) {
      canvas.removeEventListener("click", mouseClickListener);
    }
    mouseMoveListener = null;
    mouseClickListener = null;
    clearCanvas();
  }

  function initialiseMasks() {
    cleanup();
    canvas.style.zIndex = "100";

    let frameId = video.getCurrentFrameId();
    let maskList = objectNameList.map(function (_, objectId) {
      return new Mask(`/masks/${frameId}-${objectId + 1}.png`);
    });

    function findMask(e: MouseEvent): [number, Mask | null] {
      let x = (e.screenX - offsetX) / width;
      let y = (e.screenY - offsetY) / height;
      for (let [index, mask] of maskList.entries()) {
        if (mask.contains(x, y)) {
          return [index, mask];
        }
      }
      return [-1, null];
    }

    let currentMask: Mask | null = null;
    mouseMoveListener = function (e: MouseEvent) {
      let [_, found] = findMask(e);
      if (found === currentMask) {
        return;
      }
      if (currentMask === null) {
        currentMask = found;
        ctx.drawImage(found!.image, 0, 0, width, height);
      } else {
        currentMask = null;
        clearCanvas();
      }
    };

    mouseClickListener = function (e: MouseEvent) {
      e.stopPropagation();
      e.preventDefault();
      let [maskIndex, found] = findMask(e);
      if (!found) {
        // Click on background, resumes the video if it's currently paused
        if (!video.isPlaying) {
          video.resume();
        }
        return;
      }
      // Click on a mask
      if (video.isPlaying) {
        // Video is playing, ignore
        return;
      }
      alert(objectNameList[maskIndex]);
    };
    window.addEventListener("mousemove", mouseMoveListener);
    canvas.addEventListener("click", mouseClickListener);
  }

  video.addEventListener("pause", initialiseMasks);
  video.addEventListener("seeked", function () {
    if (!video.isPlaying) {
      initialiseMasks();
    }
  });
  video.addEventListener("play", cleanup);
  video.addEventListener("ended", cleanup);
};
