import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import { useSessionStore } from './stores/session'
import { setUnauthorizedHandler } from './services/http'

// Polices self-hostées (local-only, aucun CDN à l'exécution).
import '@fontsource-variable/bricolage-grotesque'
import '@fontsource-variable/hanken-grotesk'

// Design system « La Courbe » + Tailwind.
import './styles/tokens.css'

const pinia = createPinia()
const app = createApp(App).use(pinia).use(router)

const session = useSessionStore(pinia)

// Intercepteur 401 global : une session expirée en cours d'usage purge l'état et
// renvoie vers la connexion (en mémorisant la page pour y revenir). Anti-boucle
// via le flag + on ne redirige pas si on est déjà sur une page publique/d'accès.
let redirecting = false
setUnauthorizedHandler(() => {
  if (redirecting) return
  session.expire()
  const cur = router.currentRoute.value
  if (cur.meta.requiresAuth) {
    redirecting = true
    router
      .replace({ name: 'connexion', query: { redirect: cur.fullPath } })
      .finally(() => {
        redirecting = false
      })
  }
})

// Revalide la session (cookie HttpOnly → /api/auth/me) AVANT le montage, pour que
// la garde du routeur s'appuie sur l'état d'authentification réel, pas sur le cache.
session.hydrate().finally(() => app.mount('#app'))
