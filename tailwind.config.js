/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './static/js/**/*.js',
  ],
  darkMode: ['class', '.dark-mode'],  // Support both .dark and .dark-mode classes
  theme: {
    extend: {
      colors: {
        // Minimal Heritage Palette - Only essential colors
        surface: {
          DEFAULT: '#FDFCF8',
          alt: '#F5F2ED',
          dark: '#1A1410',
          'dark-alt': '#241E19',
        },
        text: {
          DEFAULT: '#2C2119',
          muted: '#6B5D52',
          dark: '#EFE5D7',
          'dark-muted': '#A89B8C',
        },
        accent: {
          DEFAULT: '#B8974F',
          hover: '#A3854A',
          muted: '#D4C4A0',
        },
        border: {
          DEFAULT: '#E5E0D8',
          dark: '#3E342E',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        serif: ['"Playfair Display"', 'Georgia', 'serif'],
      },
    },
  },
  plugins: [],
}
