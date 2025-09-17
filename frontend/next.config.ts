const API_BASE = process.env.NEXT_PUBLIC_API_BASE; 

const nextConfig = {
  async rewrites() {
    if (!API_BASE) return [];
    return [
      {
        source: '/api/:path*',
        destination: `${API_BASE}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;