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
        'dark-bg': '#181c2a',
        'dark-surface': '#23273a',
        'dark-border': '#31364a',
        'dark-text': '#e0e0e0',
        'dark-accent': '#6366f1',
        'dark-hover': '#23273a',
        // Blogforge-style tokens for Tailwind utilities
        border: 'hsl(var(--border) / <alpha-value>)',
        background: 'hsl(var(--background) / <alpha-value>)',
        foreground: 'hsl(var(--foreground) / <alpha-value>)',
        card: 'hsl(var(--card) / <alpha-value>)',
        'card-foreground': 'hsl(var(--card-foreground) / <alpha-value>)',
        popover: 'hsl(var(--popover) / <alpha-value>)',
        'popover-foreground': 'hsl(var(--popover-foreground) / <alpha-value>)',
        primary: 'hsl(var(--primary) / <alpha-value>)',
        'primary-foreground': 'hsl(var(--primary-foreground) / <alpha-value>)',
        secondary: 'hsl(var(--secondary) / <alpha-value>)',
        'secondary-foreground': 'hsl(var(--secondary-foreground) / <alpha-value>)',
        muted: 'hsl(var(--muted) / <alpha-value>)',
        'muted-foreground': 'hsl(var(--muted-foreground) / <alpha-value>)',
        accent: 'hsl(var(--accent) / <alpha-value>)',
        'accent-foreground': 'hsl(var(--accent-foreground) / <alpha-value>)',
        destructive: 'hsl(var(--destructive) / <alpha-value>)',
        'destructive-foreground': 'hsl(var(--destructive-foreground) / <alpha-value>)',
        input: 'hsl(var(--input) / <alpha-value>)',
        ring: 'hsl(var(--ring) / <alpha-value>)',
        // Sidebar tokens
        'sidebar-background': 'hsl(var(--sidebar-background) / <alpha-value>)',
        'sidebar-foreground': 'hsl(var(--sidebar-foreground) / <alpha-value>)',
        'sidebar-primary': 'hsl(var(--sidebar-primary) / <alpha-value>)',
        'sidebar-primary-foreground': 'hsl(var(--sidebar-primary-foreground) / <alpha-value>)',
        'sidebar-accent': 'hsl(var(--sidebar-accent) / <alpha-value>)',
        'sidebar-accent-foreground': 'hsl(var(--sidebar-accent-foreground) / <alpha-value>)',
        'sidebar-border': 'hsl(var(--sidebar-border) / <alpha-value>)',
        'sidebar-ring': 'hsl(var(--sidebar-ring) / <alpha-value>)',
      }
    }
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/aspect-ratio'),
  ],
  safelist: [
    // Dark theme classes
    'bg-dark-bg',
    'bg-dark-surface',
    'bg-dark-hover',
    'border-dark-border',
    'text-dark-text',
    'text-dark-accent',
    'hover:text-dark-accent',
    'hover:bg-dark-surface',
    'hover:border-dark-accent',
    'hover:bg-dark-hover',
    // Navigation specific classes
    'border-blue-500',
    'text-blue-500',
    'text-gray-400',
    'hover:text-dark-text',
    'font-medium',
    'transition-colors',
    'duration-200',
    // Active state classes
    'bg-dark-hover',
    'text-blue-500'
  ]
} 