const path = require('path')

/** @type {import('next').NextConfig} */
const nextConfig = {
  images: { unoptimized: true },
  env: {
    NEXT_PUBLIC_API_URL:
      process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  webpack: (config) => {
    config.resolve.alias['@'] = path.resolve(__dirname, '.')
    return config
  },
}

module.exports = nextConfig
