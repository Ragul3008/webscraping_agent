/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        gold: {
          50: '#fffdf0',
          100: '#fef7be',
          200: '#fdf18d',
          300: '#fbe64d',
          400: '#fad91a',
          500: '#d9b40f', // Main Gold Highlight
          600: '#b78f09',
          700: '#956d07',
          800: '#734f07',
          900: '#563a07',
          950: '#321f02',
        },
        darkbg: {
          950: '#030303',
          900: '#0a0a0a',
          800: '#141414',
          700: '#1e1e1e',
        }
      },
      backgroundImage: {
        'gold-gradient': 'linear-gradient(135deg, #fbe64d 0%, #d9b40f 50%, #956d07 100%)',
        'gold-glow': 'radial-gradient(circle, rgba(217, 180, 15, 0.15) 0%, transparent 70%)',
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
        'gold-border': '0 0 15px rgba(217, 180, 15, 0.15)',
        'gold-glow-hover': '0 0 25px rgba(217, 180, 15, 0.3)',
      },
      fontFamily: {
        sans: ['Outfit', 'Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
