/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0A0A0B",
        surface: "#121215",
        surfaceHover: "#18181D",
        borderSubtle: "rgba(255, 255, 255, 0.08)",
        primary: "#3B82F6",
        primaryHover: "#2563EB",
        accentEmerald: "#10B981",
        accentAmber: "#F59E0B",
        accentRose: "#EF4444",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
};
