import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: "#4F46E5",
        xp: "#0EA5E9"
      }
    }
  },
  plugins: []
} satisfies Config;
