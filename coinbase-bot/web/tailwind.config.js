/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        void: "#04060f",
        deep: "#070c1c",
        panel: "#0b1226",
        line: "#1b2a4d",
        neon: "#39ff8a",
        cyan: "#22e8ff",
        violet: "#a86bff",
        loss: "#ff4d6d",
      },
      fontFamily: {
        pixel: ['"Press Start 2P"', "ui-monospace", "monospace"],
        mono: ['"Space Grotesk"', "ui-monospace", "monospace"],
      },
      boxShadow: {
        neon: "0 0 12px rgba(57,255,138,.45), inset 0 0 10px rgba(57,255,138,.12)",
        cyanGlow: "0 0 12px rgba(34,232,255,.45)",
      },
    },
  },
  plugins: [],
};
