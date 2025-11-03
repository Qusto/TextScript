/** @type {import('next').NextConfig} */
const nextConfig = {
  // AICODE-NOTE: T056 - Enable standalone output for Docker deployment
  // This bundles all dependencies into .next/standalone for minimal Docker image
  output: 'standalone',
};

export default nextConfig;
