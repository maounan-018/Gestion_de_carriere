import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import { useSessionStore } from './stores/session'

// Polices self-hostées (local-only, aucun CDN à l'exécution).
import '@fontsource-variable/bricolage-grotesque'
import '@fontsource-variable/hanken-grotesk'

// Design system « La Courbe » + Tailwind.
import './styles/tokens.css'

const pinia = createPinia()
const app = createApp(App).use(pinia).use(router)

// Revalide la session (cookie HttpOnly → /api/auth/me) AVANT le montage, pour que
// la garde du routeur s'appuie sur l'état d'authentification réel, pas sur le cache.
const session = useSessionStore(pinia)
session.hydrate().finally(() => app.mount('#app'))
