import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',
  distDir: '../qtype/interpreter/ui',
  trailingSlash: true,
  images: {
    unoptimized: true
  }
};

export default nextConfig;
