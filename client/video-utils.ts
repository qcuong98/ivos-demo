function initialiseCanvasSize(): Promise<{ height: number; width: number }> {
  let container = document.getElementById("container")!;
  let canvas = document.getElementById("main-canvas") as HTMLCanvasElement;

  return new Promise(function (resolve) {
    setTimeout(function () {
      canvas.width = container.clientWidth;
      canvas.height = container.clientHeight;
      resolve({
        width: canvas.width,
        height: canvas.height
      });
    }, 500);
  });
}

export { initialiseCanvasSize };
