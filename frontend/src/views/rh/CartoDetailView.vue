<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Sparkles } from '@lucide/vue'
import { apiService } from '@/services/apiService'
import { CARTO_SKILLS } from '@/data/rh'
import type { CartoPole } from '@/types/rh'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseBreadcrumb from '@/components/ui/BaseBreadcrumb.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

const route = useRoute()
const pole = ref<CartoPole | null>(null)
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    pole.value = (await apiService.getCartoPole(route.params.pole as string)) ?? null
  } catch {
    error.value = 'Impossible de charger le pôle.'
  } finally {
    loading.value = false
  }
}
onMounted(load)
watch(() => route.params.pole, load)

const critTone: Record<string, 'hot' | 'warn' | 'new'> = { critique: 'hot', modéré: 'warn', bénin: 'new' }
</script>

<template>
  <LoadingState v-if="loading" label="Chargement du pôle…" />
  <ErrorState v-else-if="error" :message="error">
    <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
  </ErrorState>
  <EmptyState v-else-if="!pole" title="Pôle introuvable" text="Ce pôle n'existe pas.">
    <template #action>
      <RouterLink :to="{ name: 'rh.cartographie' }"><BaseButton size="sm">Retour</BaseButton></RouterLink>
    </template>
  </EmptyState>

  <div v-else>
    <BaseBreadcrumb
      :items="[{ label: 'Cartographie', to: { name: 'rh.cartographie' } }, { label: pole.name }]"
    />
    <div class="grid gap-5 lg:grid-cols-[1fr_320px]">
      <BaseCard :title="`Compétences · ${pole.name}`">
        <div class="space-y-3">
          <div v-for="(l, i) in pole.levels" :key="i">
            <div class="mb-1 flex justify-between text-xs">
              <span class="font-medium text-ink-2">{{ CARTO_SKILLS[i] }}</span>
              <span class="text-ink-3">{{ l }}/5</span>
            </div>
            <div class="h-2 overflow-hidden rounded-full bg-panel-2">
              <div class="h-full rounded-full bg-green" :style="{ width: (l / 5) * 100 + '%' }" />
            </div>
          </div>
        </div>
        <div v-if="pole.people.length" class="mt-4">
          <div class="mb-1 text-xs font-semibold text-ink-3">Collaborateurs du pôle</div>
          <div class="flex flex-wrap gap-2">
            <span v-for="n in pole.people" :key="n" class="rounded-lg bg-panel-2 px-2.5 py-1 text-xs text-ink-2">{{ n }}</span>
          </div>
        </div>
      </BaseCard>

      <BaseCard>
        <div class="mb-2 flex items-center gap-2">
          <div class="grid h-8 w-8 place-items-center rounded-lg bg-green text-white"><Sparkles :size="15" /></div>
          <h3 class="font-display text-sm font-bold text-ink">Analyse & recommandations IA</h3>
        </div>
        <div class="mb-2"><BasePill :tone="critTone[pole.analyse.criticite]">Criticité : {{ pole.analyse.criticite }}</BasePill></div>
        <p class="text-sm text-ink-2">{{ pole.analyse.text }}</p>
        <div
          v-if="pole.analyse.focus"
          class="mt-3 flex items-center gap-2 rounded-xl border border-green-line bg-green-ghost px-3 py-2 text-xs text-green-deep"
        >
          <AppIcon name="route" :size="14" /> Priorité de développement : <b>{{ pole.analyse.focus }}</b>
        </div>
      </BaseCard>
    </div>
  </div>
</template>
