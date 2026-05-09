import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      // Browser -> Vite dev server -> TextBelt.
      // Avoids CORS / network blocks of textbelt.com from localhost.
      "/api/sms": {
        target: "https://textbelt.com",
        changeOrigin: true,
        secure: true,
        rewrite: (path) => path.replace(/^\/api\/sms/, "/text"),
      },
    },
  },
});