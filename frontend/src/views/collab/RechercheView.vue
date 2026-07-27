<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Search } from 'lucide-vue-next'
import { apiService } from '@/services/apiService'
import type { Colleague } from '@/types/domain'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseChip from '@/components/ui/BaseChip.vue'
import BaseAvatar from '@/components/ui/BaseAvatar.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

const items = ref<Colleague[]>([])
const loading = ref(true)
const error = ref('')
const query = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = await apiService.getColleagues()
  } catch {
    error.value = "Impossible de charger l'annuaire."
  } finally {
    loading.value = false
  }
}
onMounted(load)

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return items.value
  return items.value.filter((c) =>
    (c.name + ' ' + c.role + ' ' + c.entity + ' ' + c.skills.join(' ')).toLowerCase().includes(q),
  )
})
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center gap-2 rounded-xl border border-border bg-paper px-3 py-2">
      <Search :size="16" class="text-ink-3" />
      <input
        v-model="query"
        type="search"
        placeholder="Rechercher par nom, métier, entité, compétence…"
        class="w-full bg-transparent text-sm outline-none placeholder:text-ink-3"
      />
    </div>
    <p class="text-xs text-ink-3">{{ filtered.length }} collègue(s) · seules les informations publiques sont visibles.</p>

    <LoadingState v-if="loading" label="Chargement de l'annuaire…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>
    <EmptyState v-else-if="filtered.length === 0" title="Aucun collègue" text="Aucun collègue ne correspond à votre recherche." />

    <div v-else class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      <div v-for="c in filtered" :key="c.id" class="rounded-2xl border border-border bg-paper p-4 shadow-card">
        <div class="flex items-center gap-3">
          <BaseAvatar :initials="c.initials" size="md" />
          <div class="min-w-0">
            <h4 class="truncate text-sm font-bold text-ink">{{ c.name }}</h4>
            <p class="truncate text-xs text-ink-3">{{ c.role }} · {{ c.entity }}</p>
          </div>
        </div>
        <div class="mt-3 flex flex-wrap gap-1.5">
          <BaseChip v-for="s in c.skills" :key="s">{{ s }}</BaseChip>
        </div>
        <RouterLink :to="{ name: 'collab.profilPublic', params: { id: c.id } }" class="mt-3 block">
          <BaseButton variant="secondary" size="sm" block><AppIcon name="user" :size="14" /> Voir le profil</BaseButton>
        </RouterLink>
      </div>
    </div>
  </div>
</template>
