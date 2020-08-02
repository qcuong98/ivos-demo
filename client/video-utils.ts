function initialiseCanvasSize() {
  let container = document.getElementById("container")!;
  let canvas = document.getElementById("main-canvas") as HTMLCanvasElement;

  canvas.width = container.clientWidth;
  canvas.height = container.clientHeight;
  return {
    width: canvas.width,
    height: canvas.height
  };
}

export { initialiseCanvasSize };
