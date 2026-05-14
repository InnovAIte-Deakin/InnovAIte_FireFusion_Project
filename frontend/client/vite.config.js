import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],

  server: {
    proxy: {
      //api call proxy
      "/api": {
        target: "http://localhost:8080",
        changeOrigin: true,
        secure: false,
      },

      //websocket connection proxy
      "/api/ws": {
        target: "ws://localhost:8080",
        ws: true,
        changeOrigin: true,
      },
    },
  },
});