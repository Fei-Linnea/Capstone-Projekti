import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* Static export – produces /out with plain HTML/JS/CSS */
  output: "export",
  /* Allow all backend origins for API image optimization (not used with export, but safe) */
  images: { unoptimized: true },
};

export default nextConfig;
