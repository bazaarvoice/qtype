import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',
  distDir: process.env.NODE_ENV === 'production' ? '../qtype/interpreter/ui' : '.next',
  basePath: '/ui',
  assetPrefix: process.env.NODE_ENV === 'production' ? "https://REWRITEME" : undefined,
  trailingSlash: true,
  images: {
    unoptimized: true
  }
};

export default nextConfig;
