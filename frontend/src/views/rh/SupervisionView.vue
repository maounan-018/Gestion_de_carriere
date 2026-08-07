<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Settings, Check, BookOpen, ChevronRight, RefreshCw, AlertTriangle } from '@lucide/vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

// Supervision DATA-DRIVEN : chaque contrôle est un scan RÉEL de la base (aucune valeur
// figée). Le bouton « Relancer l'analyse » ré-exécute le scan à la demande.
type Item = { titre: string; found: number; total: number }
const items = ref<Item[]>([])
const loading = ref(true)
const error = ref('')
const lastRun = ref('')
const { toast } = useToast()

async function scan(manual = false) {
  loading.value = true
  error.value = ''
  try {
    items.value = await apiService.getSupervision()
    lastRun.value = new Date().toLocaleString('fr-FR', { dateStyle: 'medium', timeStyle: 'short' })
    if (manual) {
      const total = items.value.reduce((s, i) => s + i.found, 0)
      toast(total > 0
        ? `Analyse relancée · ${total} anomalie${total > 1 ? 's' : ''} détectée${total > 1 ? 's' : ''}`
        : 'Analyse relancée · aucune anomalie', 'ok')
    }
  } catch {
    error.value = 'Analyse indisponible pour le moment.'
    if (manual) toast('Analyse indisponible pour le moment.', 'error')
  } finally {
    loading.value = false
  }
}
onMounted(() => scan())

const anomalies = computed(() => items.value.reduce((s, i) => s + i.found, 0))
function pct(i: Item): number {
  return i.total ? Math.round((i.found / i.total) * 100) : 0
}
</script>

<template>
  <div class="space-y-5">
    <BaseCard>
      <div class="flex flex-wrap items-center gap-3">
        <div class="grid h-10 w-10 place-items-center rounded-xl bg-green-soft text-green-deep">
          <Settings :size="18" />
        </div>
        <div class="min-w-0 flex-1">
          <h3 class="font-display text-base font-bold text-ink">Supervision de la plateforme</h3>
          <p class="text-sm text-ink-3">
            Analyse de la qualité des données talents · scans réels de la base, à la demande.
          </p>
        </div>
        <BaseButton variant="secondary" size="sm" :disabled="loading" @click="scan(true)">
          <RefreshCw :size="15" :class="loading ? 'animate-spin' : ''" /> Relancer l'analyse
        </BaseButton>
      </div>
    </BaseCard>

    <LoadingState v-if="loading" label="Analyse de la qualité des données en cours…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="scan">Réessayer</BaseButton></template>
    </ErrorState>

    <BaseCard v-else title="Résultat de l'analyse">
      <template #actions>
        <BasePill :tone="anomalies === 0 ? 'new' : 'warn'">
          {{ anomalies === 0 ? 'Aucune anomalie' : `${anomalies} anomalie(s)` }}
        </BasePill>
      </template>
      <p v-if="lastRun" class="mb-2 text-xs text-ink-3">Dernière analyse : {{ lastRun }}</p>
      <div class="divide-y divide-border">
        <div v-for="r in items" :key="r.titre" class="flex items-center gap-3 py-3">
          <div
            class="grid h-8 w-8 shrink-0 place-items-center rounded-lg"
            :class="r.found === 0 ? 'bg-green-soft text-green-deep' : 'bg-warning-soft text-warning'"
          >
            <Check v-if="r.found === 0" :size="15" />
            <AlertTriangle v-else :size="15" />
          </div>
          <div class="min-w-0 flex-1">
            <h4 class="text-sm font-bold text-ink">{{ r.titre }}</h4>
            <p class="text-xs text-ink-3">
              {{ r.found }} anomalie(s) sur {{ r.total }} contrôlé(s)<span v-if="r.found"> · {{ pct(r) }} %</span>
            </p>
          </div>
          <BasePill :tone="r.found === 0 ? 'new' : 'warn'">
            {{ r.found === 0 ? 'Conforme' : 'À traiter' }}
          </BasePill>
        </div>
      </div>
    </BaseCard>

    <RouterLink
      :to="{ name: 'rh.referentiel' }"
      class="flex items-center gap-3 rounded-2xl border border-border bg-paper p-4 shadow-card transition hover:border-green-line"
    >
      <div class="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-green-soft text-green-deep">
        <BookOpen :size="18" />
      </div>
      <div class="min-w-0 flex-1">
        <h4 class="text-sm font-bold text-ink">Référentiel &amp; génération de fiches de poste</h4>
        <p class="text-xs text-ink-3">
          Référentiels ESCO · O*NET · SFIA, cartographie départements → métiers, génération de fiches.
        </p>
      </div>
      <ChevronRight :size="18" class="shrink-0 text-ink-3" />
    </RouterLink>
  </div>
</template>
