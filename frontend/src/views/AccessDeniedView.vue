<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ShieldAlert } from '@lucide/vue'
import { useSessionStore } from '@/stores/session'
import BaseButton from '@/components/ui/BaseButton.vue'

const router = useRouter()
const session = useSessionStore()

function backHome() {
  if (session.role) router.push({ name: `${session.role}.dashboard` })
  else router.push({ name: 'connexion' })
}
</script>

<template>
  <div class="grid min-h-screen place-items-center bg-bg px-4 text-center">
    <div class="max-w-md">
      <div
        class="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-2xl bg-danger-soft text-danger"
      >
        <ShieldAlert :size="26" />
      </div>
      <h1 class="font-display text-2xl font-extrabold text-ink">Accès refusé</h1>
      <p class="mt-2 text-sm text-ink-2">
        Cet écran est réservé à un autre rôle. Vous êtes connecté en tant que
        <b>{{ session.user?.roleLabel || '—' }}</b>.
      </p>
      <BaseButton class="mt-5" @click="backHome">Retour à mon espace</BaseButton>
    </div>
  </div>
</template>
