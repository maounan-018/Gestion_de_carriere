<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { Souhait } from '@/types/domain'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseBreadcrumb from '@/components/ui/BaseBreadcrumb.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const items = ref<Souhait[]>([])
const loading = ref(true)
const error = ref('')
const { toast } = useToast()

const crumbs = [
  { label: 'Mon profil', to: { name: 'collab.profil' } },
  { label: "Souhaits d'évolution" },
]

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = (await apiService.getSouhaits()).map((s) => ({ ...s }))
  } catch {
    error.value = 'Impossible de charger vos souhaits.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

async function push(s: Souhait) {
  const prev = { pushed: s.pushed, status: s.status, tone: s.tone }
  s.pushed = true
  s.status = 'Poussé au manager'
  s.tone = 'new'
  try {
    await apiService.pushSouhait(s.id ?? '')
    toast('Souhait transmis à votre manager')
  } catch (e) {
    Object.assign(s, prev)
    toast(e instanceof Error ? e.message : "Échec de l'envoi au manager", 'error')
  }
}
</script>

<template>
  <div>
    <BaseBreadcrumb :items="crumbs" />

    <div class="mb-4 flex flex-wrap items-center gap-3 rounded-2xl border border-green-line bg-green-soft p-4">
      <div class="grid h-10 w-10 place-items-center rounded-xl bg-green text-white"><AppIcon name="route" :size="18" /></div>
      <div class="min-w-0 flex-1">
        <h3 class="text-sm font-bold text-green-deep">Vos souhaits guident vos recommandations</h3>
        <p class="text-xs text-ink-2">Les souhaits que vous poussez sont transmis à votre manager et alimentent le moteur de recommandations.</p>
      </div>
      <BaseButton @click="toast('Nouveau souhait — à venir', 'info')"><AppIcon name="route" :size="15" /> Nouveau souhait</BaseButton>
    </div>

    <LoadingState v-if="loading" label="Chargement de vos souhaits…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>

    <div v-else class="space-y-4">
      <BaseCard v-for="(s, i) in items" :key="i">
        <template #header>
          <h3 class="font-display text-base font-bold text-ink">{{ s.title }}</h3>
        </template>
        <template #actions><BasePill :tone="s.tone">{{ s.status }}</BasePill></template>

        <div class="flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-3">
          <span class="inline-flex items-center gap-1"><AppIcon name="route" :size="12" /> Horizon {{ s.horizon }}</span>
        </div>
        <p class="mt-2 text-sm text-ink-2">{{ s.desc }}</p>
        <p v-if="!s.pushed" class="mt-2 text-xs text-ink-3">Ce souhait n'est visible que par vous tant que vous ne l'avez pas poussé à votre manager.</p>

        <div class="mt-3 flex flex-wrap gap-2">
          <BaseButton variant="secondary" size="sm" @click="toast('Modification — à venir', 'info')">Modifier</BaseButton>
          <BaseButton v-if="!s.pushed" size="sm" @click="push(s)"><AppIcon name="send" :size="14" /> Pousser au manager</BaseButton>
        </div>
      </BaseCard>
    </div>
  </div>
</template>
