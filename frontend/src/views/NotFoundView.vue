<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Compass } from 'lucide-vue-next'
import BaseButton from '@/components/ui/BaseButton.vue'

const router = useRouter()
</script>

<template>
  <div class="grid min-h-screen place-items-center bg-bg px-4 text-center">
    <div class="max-w-md">
      <div
        class="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-2xl bg-green-soft text-green-deep"
      >
        <Compass :size="26" />
      </div>
      <h1 class="font-display text-2xl font-extrabold text-ink">Page introuvable</h1>
      <p class="mt-2 text-sm text-ink-2">La page demandée n'existe pas ou a été déplacée.</p>
      <BaseButton class="mt-5" @click="router.push({ name: 'portail' })">
        Retour à l'accueil
      </BaseButton>
    </div>
  </div>
</template>
