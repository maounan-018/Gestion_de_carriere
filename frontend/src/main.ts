import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'

// Polices self-hostées (local-only, aucun CDN à l'exécution).
import '@fontsource-variable/bricolage-grotesque'
import '@fontsource-variable/hanken-grotesk'

// Design system « La Courbe » + Tailwind.
import './styles/tokens.css'

createApp(App).use(createPinia()).use(router).mount('#app')
