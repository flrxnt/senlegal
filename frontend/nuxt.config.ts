import tailwindcss from "@tailwindcss/vite";

export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  modules: [
    '@pinia/nuxt',
    '@vueuse/nuxt',
    '@nuxt/image',
    '@nuxtjs/seo',
  ],

  css: ['./app/assets/css/main.css'],

  vite: {
    plugins: [tailwindcss()],
  },

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:3001/api',
      siteUrl: process.env.NUXT_PUBLIC_SITE_URL || 'http://localhost:3000',
    },
  },

  site: {
    url: process.env.NUXT_PUBLIC_SITE_URL || 'https://senlegal.sn',
    name: 'SenLégal',
    description:
      "Expertise juridique instantanée sur le Code de la Famille du Sénégal et les textes juridiques sénégalais.",
    defaultLocale: 'fr',
  },

  app: {
    head: {
      htmlAttrs: { lang: 'fr' },
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' },
      ],
      meta: [
        { name: 'theme-color', content: '#00853F' },
      ],
    },
  },

  // Pages authentifiées : rendu client uniquement (le token n'existe pas en SSR initial).
  routeRules: {
    '/app/**': { ssr: false },
    '/dashboard/**': { ssr: false },
    '/admin/**': { ssr: false },
    '/billing/**': { ssr: false },
  },

  sitemap: {
    exclude: [
      '/app/**',
      '/dashboard/**',
      '/admin/**',
      '/billing/**',
      '/login',
      '/forgot-password',
      '/reset-password',
    ],
  },

  robots: {
    disallow: ['/app/', '/dashboard/', '/admin/', '/billing/'],
  },

  image: {
    domains: ['images.unsplash.com'],
  },

  typescript: {
    strict: true,
  },
})
