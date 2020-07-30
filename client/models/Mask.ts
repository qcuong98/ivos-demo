class Mask {
  image: HTMLImageElement;
  height: number;
  width: number;
  ctx: CanvasRenderingContext2D | null;

  constructor(src: string) {
    this.image = new Image();
    this.image.src = src;
    this.image.onload = () => {
      this.savePixelDataToMemory(this.image);
    };

    this.height = 0;
    this.width = 0;
    this.ctx = null;
  }

  savePixelDataToMemory(image: HTMLImageElement) {
    let { height, width } = image;
    let canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;

    this.height = height;
    this.width = width;

    this.ctx = canvas.getContext("2d");
    this.ctx?.drawImage(image, 0, 0, width, height);
  }

  contains(x: number, y: number) {
    if (!this.ctx) {
      return false;
    }
    let actualX = Math.round(x * this.width);
    let actualY = Math.round(y * this.height);
    return this.ctx.getImageData(actualX, actualY, 1, 1).data[3] > 0;
  }
}

export default Mask;
