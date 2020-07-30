import typescript from "@rollup/plugin-typescript";
import path from "path";

export default {
  input: "client/index.ts",
  output: {
    dir: path.join("server", "public"),
    format: "cjs"
  },
  plugins: [typescript()]
};
