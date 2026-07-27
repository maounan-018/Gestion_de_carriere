<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Check, Sparkles } from 'lucide-vue-next'
import { useSessionStore } from '@/stores/session'
import BaseButton from '@/components/ui/BaseButton.vue'

const router = useRouter()
const session = useSessionStore()

async function enter() {
  // Un nouvel arrivant qui termine l'onboarding est un collaborateur.
  await session.login('collab')
  router.push({ name: 'collab.dashboard' })
}
</script>

<template>
  <div class="grid min-h-screen place-items-center bg-bg px-4">
    <div class="w-full max-w-lg text-center">
      <div
        class="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-2xl bg-green-soft text-green-deep"
      >
        <Check :size="28" />
      </div>
      <h1 class="font-display text-2xl font-extrabold text-ink">
        Bienvenue dans votre outil de carrière <span class="text-green">BMCI</span>.
      </h1>
      <p class="mt-2 text-ink-2">
        Votre profil est prêt, Marc. Explorez la mobilité interne, suivez vos formations et préparez
        vos entretiens avec le Coach Carrière.
      </p>
      <div
        class="mt-5 inline-flex items-center gap-2 rounded-full bg-green-ghost px-3 py-1 text-xs font-semibold text-green-deep"
      >
        <Sparkles :size="13" /> Coach Carrière · un conseil personnalisé vous attend
      </div>
      <div class="mt-6">
        <BaseButton :disabled="session.loading" @click="enter">
          {{ session.loading ? 'Connexion…' : 'Accéder à mon espace →' }}
        </BaseButton>
      </div>
    </div>
  </div>
</template>
