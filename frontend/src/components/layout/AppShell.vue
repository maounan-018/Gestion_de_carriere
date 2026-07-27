<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useSessionStore } from '@/stores/session'
import { NAV_CONFIG } from '@/config/nav'
import AppSidebar from './AppSidebar.vue'
import AppTopBar from './AppTopBar.vue'

const session = useSessionStore()
const route = useRoute()
const nav = computed(() => (session.role ? NAV_CONFIG[session.role] : []))

// Tiroir mobile : fermé par défaut, refermé à chaque changement de route.
const sidebarOpen = ref(false)
watch(() => route.fullPath, () => (sidebarOpen.value = false))
</script>

<template>
  <div class="flex min-h-screen bg-bg">
    <a
      href="#contenu-principal"
      class="sr-only focus:not-sr-only focus:absolute focus:left-3 focus:top-3 focus:z-50 focus:rounded-lg focus:bg-green focus:px-3 focus:py-2 focus:text-sm focus:font-semibold focus:text-white"
    >
      Aller au contenu
    </a>

    <AppSidebar :items="nav" :open="sidebarOpen" @close="sidebarOpen = false" />

    <div class="flex min-w-0 flex-1 flex-col">
      <AppTopBar @toggle-sidebar="sidebarOpen = !sidebarOpen" />
      <main id="contenu-principal" class="flex-1 overflow-x-auto px-4 py-6 sm:px-6">
        <div class="mx-auto max-w-6xl">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>
