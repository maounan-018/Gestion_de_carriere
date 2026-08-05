<script setup lang="ts">
import { useRoute } from 'vue-router'
import AuthCard from '@/components/access/AuthCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'

const route = useRoute()
</script>

<template>
  <AuthCard>
    <h1 class="font-display text-xl font-bold text-ink">
      {{ (route.meta.title as string) || 'Accès' }}
    </h1>
    <p class="mt-2 text-sm text-ink-2">
      Écran d'accès en cours de construction · il sera finalisé dans la suite de M2 (inscription,
      OTP, onboarding, mot de passe oublié).
    </p>
    <div class="mt-5 flex gap-2">
      <BaseButton variant="secondary" size="sm" @click="$router.push({ name: 'portail' })">
        ← Portail
      </BaseButton>
      <BaseButton size="sm" @click="$router.push({ name: 'connexion' })">
        Aller à la connexion
      </BaseButton>
    </div>
  </AuthCard>
</template>
