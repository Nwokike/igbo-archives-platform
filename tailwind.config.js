/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './core/templates/**/*.html',
    './archives/templates/**/*.html',
    './books/templates/**/*.html',
    './insights/templates/**/*.html',
    './users/templates/**/*.html',

    './ai/templates/**/*.html',
    './core/static/js/**/*.js',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        sepia: {
          DEFAULT: '#B8A88A',
          light: '#CDA882',
          mid: '#D4B595',
          soft: '#DCC1A7',
          pale: '#E3CEB9',
          cream: '#EADBCB',
        },
        heritage: {
          cream: '#F0F0DA',
          warm: '#EAE8BA',
          parchment: '#D6CE9B',
          sand: '#C5B78D',
          tan: '#B4A77E',
        },
        vintage: {
          bone: '#E4DDD0',
          white: '#EFE5D7',
          dun: '#EED6B9',
          tan: '#D1AF89',
          beaver: '#9D896E',
          gold: '#B8974F',
          bronze: '#9D7A3E',
          brass: '#8C7040',
          olive: '#8A8051',
        },
        dark: {
          bronze: '#8C6433',
          umber: '#6A2D01',
          brown: '#3D2817',
        },
        primary: {
          50: '#FDF8F3',
          100: '#FAEEE3',
          200: '#F5DCC8',
          300: '#EFC9AD',
          400: '#E0A877',
          500: '#D18741',
          600: '#B8974F',
          700: '#9D7A3E',
          800: '#8C7040',
          900: '#6A2D01',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'system-ui', 'sans-serif'],
        serif: ['Playfair Display', 'Georgia', 'serif'],
        display: ['Playfair Display', 'Georgia', 'serif'],
      },
      fontSize: {
        'display-xl': ['3rem', { lineHeight: '1.2', fontWeight: '600' }],
        'display-lg': ['2.25rem', { lineHeight: '1.25', fontWeight: '600' }],
        'display-md': ['1.75rem', { lineHeight: '1.3', fontWeight: '600' }],
        'display-sm': ['1.5rem', { lineHeight: '1.35', fontWeight: '600' }],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '112': '28rem',
        '128': '32rem',
      },
      borderRadius: {
        'xl': '1rem',
        '2xl': '1.5rem',
        '3xl': '2rem',
      },
      boxShadow: {
        'soft': '0 2px 20px rgba(61, 40, 23, 0.08)',
        'soft-lg': '0 4px 30px rgba(61, 40, 23, 0.12)',
        'soft-hover': '0 8px 40px rgba(61, 40, 23, 0.15)',
        'card': '0 1px 3px rgba(61, 40, 23, 0.05), 0 4px 12px rgba(61, 40, 23, 0.08)',
        'card-hover': '0 4px 8px rgba(61, 40, 23, 0.08), 0 12px 24px rgba(61, 40, 23, 0.12)',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'fade-in-up': 'fadeInUp 0.4s ease-out',
        'slide-in-right': 'slideInRight 0.3s ease-out',
        'slide-in-left': 'slideInLeft 0.3s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
        'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        slideInLeft: {
          '0%': { opacity: '0', transform: 'translateX(-20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        pulseSoft: {
          '0%, 100%': { transform: 'scale(1)', boxShadow: '0 0 0 0 rgba(184, 151, 79, 0.4)' },
          '50%': { transform: 'scale(1.02)', boxShadow: '0 0 0 8px rgba(184, 151, 79, 0)' },
        },
      },
      transitionTimingFunction: {
        'smooth': 'cubic-bezier(0.4, 0, 0.2, 1)',
        'bounce-in': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
      },
      backgroundImage: {
        'gradient-vintage': 'linear-gradient(135deg, #B8974F 0%, #9D7A3E 100%)',
        'gradient-heritage': 'linear-gradient(135deg, #F0F0DA 0%, #E3CEB9 100%)',
        'gradient-dark': 'linear-gradient(135deg, #3D2817 0%, #1A1410 100%)',
      },
    },
  },
  plugins: [],
}
