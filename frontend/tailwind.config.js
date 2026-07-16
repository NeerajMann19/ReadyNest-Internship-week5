/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "var(--border-color)",
        background: "var(--bg-primary)",
        surface: "var(--bg-surface)",
        foreground: "var(--text-primary)",
        primary: {
          DEFAULT: "var(--brand-blue)",
          foreground: "#ffffff",
        },
        secondary: {
          DEFAULT: "var(--bg-secondary)",
          foreground: "var(--text-secondary)",
        },
        accent: {
          DEFAULT: "var(--accent-cyan)",
          foreground: "#ffffff",
        },
        violet: "var(--brand-violet)",
        success: "var(--status-success)",
        warning: "var(--status-warning)",
        danger: "var(--status-danger)",
        info: "var(--status-info)",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        heading: ["Space Grotesk", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      borderRadius: {
        small: "8px",
        button: "12px",
        card: "16px",
        dialog: "20px",
      },
    },
  },
  plugins: [],
}
