<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { Colleague } from '@/types/domain'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseChip from '@/components/ui/BaseChip.vue'
import BaseAvatar from '@/components/ui/BaseAvatar.vue'
import BaseBreadcrumb from '@/components/ui/BaseBreadcrumb.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

const route = useRoute()
const { toast } = useToast()
const person = ref<Colleague | null>(null)
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    person.value = (await apiService.getColleague(route.params.id as string)) ?? null
  } catch {
    error.value = 'Impossible de charger ce profil.'
  } finally {
    loading.value = false
  }
}
onMounted(load)
watch(() => route.params.id, load)
</script>

<template>
  <LoadingState v-if="loading" label="Chargement du profil…" />
  <ErrorState v-else-if="error" :message="error">
    <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
  </ErrorState>
  <EmptyState v-else-if="!person" title="Profil introuvable" text="Ce collègue n'est pas dans l'annuaire.">
    <template #action>
      <RouterLink :to="{ name: 'collab.recherche' }"><BaseButton size="sm">Retour à l'annuaire</BaseButton></RouterLink>
    </template>
  </EmptyState>

  <div v-else>
    <BaseBreadcrumb :items="[{ label: 'Rechercher', to: { name: 'collab.recherche' } }, { label: person.name }]" />

    <BaseCard class="mb-5">
      <div class="flex flex-wrap items-center gap-4">
        <BaseAvatar :initials="person.initials" size="xl" />
        <div class="min-w-0 flex-1">
          <h2 class="font-display text-xl font-bold text-ink">{{ person.name }}</h2>
          <p class="text-sm text-ink-3">{{ person.role }} · {{ person.entity }}</p>
          <div class="mt-1.5 flex flex-wrap gap-x-4 text-xs text-ink-3">
            <span class="inline-flex items-center gap-1"><AppIcon name="pin" :size="12" /> Groupe BMCI</span>
            <span class="inline-flex items-center gap-1"><AppIcon name="shield" :size="12" /> Profil public</span>
          </div>
        </div>
        <BaseButton @click="toast('Message envoyé à ' + person.name.split(' ')[0])">
          <AppIcon name="mail" :size="15" /> Contacter
        </BaseButton>
      </div>
    </BaseCard>

    <div class="mb-5 flex items-start gap-2 rounded-xl border border-green-line bg-green-ghost px-3.5 py-2.5 text-xs text-green-deep">
      <AppIcon name="shield" :size="14" />
      Vous consultez les informations publiques de ce profil. Les données de carrière détaillées restent privées.
    </div>

    <div class="grid gap-5 lg:grid-cols-2">
      <BaseCard title="Compétences publiques">
        <div class="flex flex-wrap gap-2">
          <BaseChip v-for="s in person.skills" :key="s" tone="green">{{ s }}</BaseChip>
        </div>
      </BaseCard>
      <BaseCard title="À propos">
        <p class="text-sm leading-relaxed text-ink-2">
          {{ person.name }} exerce comme {{ person.role.toLowerCase() }} au sein de {{ person.entity }}.
          Ce profil partage publiquement ses principales compétences pour faciliter les mises en
          relation et la mobilité interne au sein du Groupe.
        </p>
      </BaseCard>
    </div>
  </div>
</template>
