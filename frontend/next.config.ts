import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    /*
     * Account pictures in the sidebar footer.
     *
     * Clerk serves every avatar from its own CDN, including the generated
     * initials image for accounts that never uploaded one, so this single
     * host covers the lot. Scoped to that host rather than left open: an
     * unrestricted `remotePatterns` turns `/_next/image` into an open proxy.
     */
    remotePatterns: [{ protocol: "https", hostname: "img.clerk.com", pathname: "/**" }],
  },
};

export default nextConfig;
