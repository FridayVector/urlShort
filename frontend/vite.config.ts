import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const API_TARGET = process.env.VITE_API_URL || "http://localhost:8000";
const ALLOWED_HOSTS = (process.env.VITE_ALLOWED_HOSTS || "localhost,127.0.0.1").split(",");

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    allowedHosts: ALLOWED_HOSTS,
    proxy: {
      "/api": {
        target: API_TARGET,
        changeOrigin: true,
      },
    },
  },
});
