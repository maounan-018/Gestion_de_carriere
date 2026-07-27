<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Lock, Mail } from 'lucide-vue-next'
import { useSessionStore } from '@/stores/session'
import { PERSONAS } from '@/data/personas'
import type { Role } from '@/types/domain'
import AuthCard from '@/components/access/AuthCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'

const router = useRouter()
const route = useRoute()
const session = useSessionStore()

const roles: { value: Role; label: string }[] = [
  { value: 'collab', label: 'Collaborateur' },
  { value: 'manager', label: 'Manager' },
  { value: 'rh', label: 'RH' },
]
const selectedRole = ref<Role>('collab')
const email = ref(PERSONAS.collab.email)
const password = ref('MotDePasse1!')

function onRole(r: Role) {
  selectedRole.value = r
  email.value = PERSONAS[r].email
}

async function submit() {
  await session.login(selectedRole.value, email.value, password.value)
  const redirect = route.query.redirect as string | undefined
  router.push(redirect || { name: `${selectedRole.value}.dashboard` })
}
</script>

<template>
  <AuthCard>
    <h1 class="font-display text-xl font-bold text-ink">Bon retour parmi nous</h1>
    <p class="mt-1 text-sm text-ink-3">Entrez vos identifiants pour accéder à votre espace.</p>

    <form class="mt-5 space-y-4" @submit.prevent="submit">
      <div>
        <label for="cnx-email" class="mb-1 block text-xs font-semibold text-ink-2">E-mail professionnel</label>
        <div
          class="flex items-center gap-2 rounded-xl border border-border bg-paper px-3 focus-within:border-green-line"
        >
          <Mail :size="16" class="text-ink-3" />
          <input
            id="cnx-email"
            v-model="email"
            type="email"
            autocomplete="username"
            class="w-full bg-transparent py-2.5 text-sm text-ink outline-none"
          />
        </div>
      </div>

      <div>
        <label for="cnx-password" class="mb-1 block text-xs font-semibold text-ink-2">Mot de passe</label>
        <div
          class="flex items-center gap-2 rounded-xl border border-border bg-paper px-3 focus-within:border-green-line"
        >
          <Lock :size="16" class="text-ink-3" />
          <input
            id="cnx-password"
            v-model="password"
            type="password"
            autocomplete="current-password"
            class="w-full bg-transparent py-2.5 text-sm text-ink outline-none"
          />
        </div>
      </div>

      <!-- Sélecteur d'espace DÉMO : unifie les 3 maquettes (collab/manager/RH) -->
      <div class="rounded-xl border border-dashed border-gold/40 bg-gold-soft/40 p-3">
        <div class="mb-2 text-[11px] font-bold uppercase tracking-wide text-gold">
          Démonstration · choisir l'espace
        </div>
        <div class="grid grid-cols-3 gap-1.5">
          <button
            v-for="r in roles"
            :key="r.value"
            type="button"
            class="rounded-lg px-2 py-1.5 text-xs font-semibold transition"
            :class="
              selectedRole === r.value
                ? 'bg-green text-white shadow-green'
                : 'border border-border bg-paper text-ink-2 hover:text-ink'
            "
            @click="onRole(r.value)"
          >
            {{ r.label }}
          </button>
        </div>
      </div>

      <BaseButton type="submit" block :disabled="session.loading">
        <Lock :size="16" /> {{ session.loading ? 'Connexion…' : 'Se connecter' }}
      </BaseButton>

      <div class="flex items-center justify-between text-xs">
        <button
          type="button"
          class="text-ink-3 hover:text-green-deep"
          @click="router.push({ name: 'motDePasseOublie' })"
        >
          Mot de passe oublié ?
        </button>
        <button
          type="button"
          class="font-semibold text-green-deep hover:underline"
          @click="router.push({ name: 'inscription' })"
        >
          Créer un compte
        </button>
      </div>
    </form>
  </AuthCard>
</template>
