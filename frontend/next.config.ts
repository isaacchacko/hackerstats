import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  env: {
    NEO4J_URI: process.env.NEO4J_URI,
    NEO4J_USERNAME: process.env.NEO4J_USERNAME,
    NEO4J_PASSWORD: process.env.NEO4J_PASSWORD,
    NEO4J_DATABASE: process.env.NEO4J_DATABASE,
    AURA_INSTANCEID: process.env.AURA_INSTANCEID,
    AURA_INSTANCENAME: process.env.AURA_INSTANCENAME,
  },
};

export default nextConfig;
