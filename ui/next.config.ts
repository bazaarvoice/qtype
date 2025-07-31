import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',
  distDir: process.env.NODE_ENV === 'production' ? '../qtype/interpreter/ui' : '.next',
  basePath: '/ui',
  trailingSlash: true,
  images: {
    unoptimized: true
  }
};

export default nextConfig;
