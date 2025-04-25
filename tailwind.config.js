/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/templates/**/*.html",
    "./app/static/js/**/*.js",
    "./app/static/css/src/**/*.css"
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'dark-bg': '#1a1a1a',
        'dark-surface': '#2d2d2d',
        'dark-border': '#404040',
        'dark-text': '#e0e0e0',
        'dark-accent': '#6366f1'
      }
    }
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/aspect-ratio'),
  ],
  safelist: [
    'bg-dark-bg',
    'bg-dark-surface',
    'border-dark-border',
    'text-dark-text',
    'text-dark-accent',
    'hover:text-dark-accent'
  ]
} 