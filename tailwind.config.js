/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './static/js/**/*.js',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        sepia: {
          DEFAULT: 'var(--color-sepia)',
          light: 'var(--color-sepia-light)',
          mid: 'var(--color-sepia-mid)',
          soft: 'var(--color-sepia-soft)',
          pale: 'var(--color-sepia-pale)',
          cream: 'var(--color-sepia-cream)',
        },
        heritage: {
          cream: 'var(--color-heritage-cream)',
          warm: 'var(--color-heritage-warm)',
          parchment: 'var(--color-heritage-parchment)',
          sand: 'var(--color-heritage-sand)',
          tan: 'var(--color-heritage-tan)',
        },
        vintage: {
          bone: 'var(--color-vintage-bone)',
          white: 'var(--color-vintage-white)',
          dun: 'var(--color-vintage-dun)',
          tan: 'var(--color-vintage-tan)',
          beaver: 'var(--color-vintage-beaver)',
          gold: 'var(--color-vintage-gold)',
          bronze: 'var(--color-vintage-bronze)',
          brass: 'var(--color-vintage-brass)',
          olive: 'var(--color-vintage-olive)',
        },
        dark: {
          bronze: 'var(--color-dark-bronze)',
          umber: 'var(--color-dark-umber)',
          brown: 'var(--color-dark-brown)',
        },
        primary: {
          50: 'var(--color-primary-50)',
          100: 'var(--color-primary-100)',
          200: 'var(--color-primary-200)',
          300: 'var(--color-primary-300)',
          400: 'var(--color-primary-400)',
          500: 'var(--color-primary-500)',
          600: 'var(--color-primary-600)',
          700: 'var(--color-primary-700)',
          800: 'var(--color-primary-800)',
          900: 'var(--color-primary-900)',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'system-ui', 'sans-serif'],
        serif: ['Playfair Display', 'Georgia', 'serif'],
        display: ['Playfair Display', 'Georgia', 'serif'],
      },
      fontSize: {
        // Refined display sizes - smaller for professional look
        'display-xl': ['2.5rem', { lineHeight: '1.15', fontWeight: '600', letterSpacing: '-0.02em' }],
        'display-lg': ['1.875rem', { lineHeight: '1.2', fontWeight: '600', letterSpacing: '-0.01em' }],
        'display-md': ['1.5rem', { lineHeight: '1.25', fontWeight: '600' }],
        'display-sm': ['1.25rem', { lineHeight: '1.3', fontWeight: '600' }],
        // Tighter body text
        'body-lg': ['1rem', { lineHeight: '1.6' }],
        'body': ['0.9375rem', { lineHeight: '1.6' }],
        'body-sm': ['0.875rem', { lineHeight: '1.5' }],
        'caption': ['0.8125rem', { lineHeight: '1.4' }],
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
