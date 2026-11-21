/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXT_PUBLIC_USER_MANAGEMENT_URL: process.env.NEXT_PUBLIC_USER_MANAGEMENT_URL || 'http://localhost:8001',
    NEXT_PUBLIC_PERSONAL_ADMIN_URL: process.env.NEXT_PUBLIC_PERSONAL_ADMIN_URL || 'http://localhost:8002',
    NEXT_PUBLIC_SYSTEM_ADMIN_URL: process.env.NEXT_PUBLIC_SYSTEM_ADMIN_URL || 'http://localhost:8003',
    NEXT_PUBLIC_OPPORTUNITY_SERVICE_URL: process.env.NEXT_PUBLIC_OPPORTUNITY_SERVICE_URL || 'http://localhost:8004',
    NEXT_PUBLIC_SCOUT_AGENT_URL: process.env.NEXT_PUBLIC_SCOUT_AGENT_URL || 'http://localhost:8005',
    NEXT_PUBLIC_RELOCATION_AGENT_URL: process.env.NEXT_PUBLIC_RELOCATION_AGENT_URL || 'http://localhost:8006',
    NEXT_PUBLIC_APPLICATION_COACH_AGENT_URL: process.env.NEXT_PUBLIC_APPLICATION_COACH_AGENT_URL || 'http://localhost:8007',
  },
};
export default nextConfig;
