import typescript from "@rollup/plugin-typescript";
import path from "path";

export default {
  input: ["client/video.ts"],
  output: {
    dir: path.join("server", "static"),
    format: "cjs"
  },
  plugins: [typescript()]
};
