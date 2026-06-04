/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace"],
      },
      colors: {
        surface: {
          DEFAULT: "#111827",
          elevated: "#1a2236",
          input: "#0c0f1a",
        },
      },
      boxShadow: {
        glow: "0 0 80px -20px rgba(99, 102, 241, 0.45)",
      },
    },
  },
  plugins: [],
};
