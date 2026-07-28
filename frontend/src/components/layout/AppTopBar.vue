<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Bell, Menu, Settings } from '@lucide/vue'
import { useSessionStore } from '@/stores/session'
import BaseBadge from '@/components/ui/BaseBadge.vue'
import BaseAvatar from '@/components/ui/BaseAvatar.vue'

defineEmits<{ 'toggle-sidebar': [] }>()
const route = useRoute()
const session = useSessionStore()
const title = computed(() => (route.meta.title as string) || 'BMCI Carrière')
const subtitle = computed(() => (route.meta.subtitle as string) || '')
const notifRoute = computed(() =>
  session.role ? { name: `${session.role}.notifications` } : { name: 'appRoot' },
)
</script>

<template>
  <header
    class="sticky top-0 z-20 flex items-center gap-2 border-b border-border bg-paper/80 px-4 py-3 backdrop-blur sm:gap-3 sm:px-6"
  >
    <button
      class="grid h-9 w-9 place-items-center rounded-xl text-ink-2 transition hover:bg-panel-2 lg:hidden"
      aria-label="Ouvrir le menu"
      @click="$emit('toggle-sidebar')"
    >
      <Menu :size="18" />
    </button>

    <div class="min-w-0">
      <div class="truncate font-display text-base font-bold text-ink">{{ title }}</div>
      <div v-if="subtitle" class="truncate text-xs text-ink-3">{{ subtitle }}</div>
    </div>

    <div class="flex-1" />

    <span v-if="session.user" class="hidden sm:block">
      <BaseBadge tone="mut">{{ session.user.roleLabel }}</BaseBadge>
    </span>

    <RouterLink
      :to="{ name: 'parametres' }"
      class="grid h-9 w-9 place-items-center rounded-xl text-ink-2 transition hover:bg-panel-2"
      aria-label="Paramètres"
    >
      <Settings :size="18" />
    </RouterLink>

    <RouterLink
      :to="notifRoute"
      class="grid h-9 w-9 place-items-center rounded-xl text-ink-2 transition hover:bg-panel-2"
      aria-label="Notifications"
    >
      <Bell :size="18" />
    </RouterLink>

    <BaseAvatar
      v-if="session.user"
      :initials="session.user.initials"
      size="md"
      :photo="session.user.photo"
    />
  </header>
</template>
