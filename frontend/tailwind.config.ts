import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        night: {
          950: "#070914",
          900: "#0b1020",
          800: "#11182d",
          700: "#19233d"
        },
        aurora: {
          cyan: "#7dd3fc",
          violet: "#a78bfa",
          mint: "#6ee7b7"
        }
      },
      boxShadow: {
        glow: "0 0 32px rgba(125, 211, 252, 0.12)"
      }
    }
  },
  plugins: []
};

export default config;

