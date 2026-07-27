<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { LogOut, X, ScrollText } from 'lucide-vue-next'
import type { NavItem } from '@/types/ui'
import { useSessionStore } from '@/stores/session'

const props = defineProps<{ items: NavItem[]; open?: boolean }>()
const emit = defineEmits<{ close: [] }>()
const route = useRoute()
const router = useRouter()
const session = useSessionStore()

// Décalage du tiroir (mobile uniquement). Sur ≥ lg, la règle CSS
// `transform: none !important` (media query) neutralise cette valeur inline —
// l'!important auteur l'emporte sur le style inline normal — donc la colonne
// reste toujours visible sur grand écran, sans dépendre de JS.
const drawerStyle = computed(() => ({
  transform: props.open ? 'translateX(0)' : 'translateX(-100%)',
}))

async function logout() {
  await session.logout()
  router.push({ name: 'portail' })
}
</script>

<template>
  <!-- Voile (mobile uniquement) -->
  <div
    v-if="open"
    class="backdrop-fade fixed inset-0 z-30 bg-ink/30 lg:hidden"
    aria-hidden="true"
    @click="emit('close')"
  />

  <aside
    class="drawer z-40 flex w-64 shrink-0 flex-col gap-1 border-r border-border bg-paper px-3 py-4 lg:z-auto"
    :style="drawerStyle"
    aria-label="Navigation principale"
  >
    <div class="mb-4 flex items-center gap-2.5 px-2">
      <div
        class="grid h-9 w-9 place-items-center rounded-xl bg-green font-display text-lg font-extrabold text-white"
      >
        B
      </div>
      <div class="min-w-0 flex-1">
        <div class="truncate text-sm font-bold text-ink">BMCI · Gestion de carrière</div>
        <div class="text-[10.5px] text-ink-3">Groupe BNP Paribas</div>
      </div>
      <button
        class="grid h-8 w-8 place-items-center rounded-lg text-ink-3 transition hover:bg-panel-2 lg:hidden"
        aria-label="Fermer le menu"
        @click="emit('close')"
      >
        <X :size="18" />
      </button>
    </div>

    <router-link
      v-for="it in items"
      :key="it.name"
      :to="{ name: it.name }"
      class="flex items-center gap-2.5 rounded-xl px-3 py-2 text-sm font-medium transition"
      :class="
        route.name === it.name
          ? 'bg-green-soft text-green-deep font-semibold'
          : 'text-ink-2 hover:bg-green-ghost hover:text-ink'
      "
      :aria-current="route.name === it.name ? 'page' : undefined"
      @click="emit('close')"
    >
      <component :is="it.icon" :size="18" />
      <span>{{ it.label }}</span>
    </router-link>

    <div class="mt-auto space-y-1 border-t border-border pt-2">
      <router-link
        :to="{ name: 'mentionsLegales' }"
        class="flex items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-ink-3 transition hover:bg-panel-2 hover:text-ink"
      >
        <ScrollText :size="16" />
        <span>Mentions légales & crédits</span>
      </router-link>
      <button
        class="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-sm font-medium text-ink-3 transition hover:bg-panel-2 hover:text-ink"
        @click="logout"
      >
        <LogOut :size="18" />
        <span>Déconnexion</span>
      </button>
    </div>
  </aside>
</template>

<style scoped>
/* Positionnement du tiroir : fixe et plein hauteur sous « lg », statique au-delà.
   Le décalage (translateX) est appliqué en inline depuis le script — priorité
   sur la cascade. Ouverture instantanée ; c'est le voile qui porte l'animation. */
.drawer {
  position: fixed;
  inset-block: 0;
  left: 0;
}
@media (min-width: 1024px) {
  .drawer {
    position: static;
    transform: none !important;
  }
}

/* Voile : fondu d'apparition (les transitions d'opacité sont fiables ici). */
.backdrop-fade {
  animation: backdrop-in 0.18s ease;
}
@media (prefers-reduced-motion: reduce) {
  .backdrop-fade {
    animation: none;
  }
}
@keyframes backdrop-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>
