<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { LayoutGrid } from '@lucide/vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { TeamMember } from '@/types/manager'
import type { CartoMatrix } from '@/types/rh'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseAvatar from '@/components/ui/BaseAvatar.vue'
import Heatmap from '@/components/shared/Heatmap.vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const team = ref<TeamMember[]>([])
const loading = ref(true)
const error = ref('')
const { toast } = useToast()

// Cartographie de l'équipe (même nomenclature que la carto RH), chargée à la demande.
const carto = ref<CartoMatrix | null>(null)
const showCarto = ref(false)
const cartoLoading = ref(false)

async function load() {
  loading.value = true
  error.value = ''
  try {
    team.value = await apiService.getTeam()
  } catch {
    error.value = 'Impossible de charger votre équipe.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

async function toggleCarto() {
  showCarto.value = !showCarto.value
  if (showCarto.value && !carto.value) {
    cartoLoading.value = true
    try {
      carto.value = await apiService.getTeamCarto()
    } finally {
      cartoLoading.value = false
    }
  }
}

// Communiquer aux RH : compose un message → crée une notification pour les RH.
const showRhMsg = ref(false)
const rhSujet = ref('')
const rhMessage = ref('')
const rhSending = ref(false)
async function sendRh() {
  if (!rhMessage.value.trim() || rhSending.value) return
  rhSending.value = true
  try {
    const r = await apiService.communiquerRH(rhSujet.value, rhMessage.value)
    toast(`Message envoyé aux RH (${r.destinataires} destinataire${r.destinataires > 1 ? 's' : ''}).`, 'ok')
    showRhMsg.value = false
    rhSujet.value = ''
    rhMessage.value = ''
  } catch {
    toast("Échec de l'envoi. Réessayez.", 'error')
  } finally {
    rhSending.value = false
  }
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <p class="text-sm text-ink-3">
        <b class="text-ink-2">{{ team.length }} collaborateurs</b> · cliquez un membre pour ouvrir
        sa base de connaissance.
      </p>
      <div class="flex gap-2">
        <BaseButton variant="secondary" size="sm" @click="toggleCarto">
          <LayoutGrid :size="15" /> {{ showCarto ? 'Masquer la cartographie' : 'Cartographie de l’équipe' }}
        </BaseButton>
        <BaseButton variant="secondary" size="sm" @click="showRhMsg = true">
          Communiquer aux RH
        </BaseButton>
      </div>
    </div>

    <!-- Cartographie de l'équipe : mêmes familles que la carto RH, lignes = membres. -->
    <div v-if="showCarto" class="rounded-2xl border border-border bg-paper p-4 shadow-card">
      <div class="mb-2 flex items-center justify-between">
        <h3 class="font-display text-base font-bold text-ink">Cartographie des compétences de l'équipe</h3>
        <span class="text-[11px] text-ink-3">niveau moyen par famille (1→5)</span>
      </div>
      <LoadingState v-if="cartoLoading" label="Chargement de la cartographie…" />
      <Heatmap v-else-if="carto && carto.lignes.length" :familles="carto.familles" :lignes="carto.lignes" />
      <p v-else class="text-sm text-ink-3">Aucune compétence évaluée pour cette équipe pour le moment.</p>
    </div>

    <LoadingState v-if="loading" label="Chargement de l'équipe…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>

    <div v-else class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      <RouterLink
        v-for="m in team"
        :key="m.id"
        :to="{ name: 'manager.ficheCollab', params: { id: m.id } }"
        class="rounded-2xl border border-border bg-paper p-4 shadow-card transition hover:-translate-y-0.5 hover:border-green-line hover:shadow-float"
      >
        <div class="flex items-center gap-3">
          <BaseAvatar :initials="m.initials" size="md" />
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-1.5">
              <h4 class="truncate text-sm font-bold text-ink">{{ m.name }}</h4>
              <BasePill v-if="m.flag === 'top'" tone="new">Haut potentiel</BasePill>
              <BasePill v-else-if="m.flag === 'watch'" tone="warn">À suivre</BasePill>
            </div>
            <p class="truncate text-xs text-ink-3">{{ m.role }} · {{ m.seniority }}</p>
          </div>
        </div>
        <div class="mt-3 flex items-center justify-between text-xs">
          <span class="text-ink-3">Éval : <b class="text-ink-2">{{ m.evalScore }}</b></span>
          <span class="font-display text-sm font-bold text-green-deep">{{ m.ring }}%</span>
        </div>
        <div class="mt-1 h-1.5 overflow-hidden rounded-full bg-panel-2">
          <div class="h-full rounded-full bg-green" :style="{ width: m.ring + '%' }" />
        </div>
      </RouterLink>
    </div>

    <BaseModal v-model="showRhMsg" title="Communiquer aux RH">
      <div class="space-y-3">
        <p class="text-xs text-ink-3">Votre message crée une notification pour l'équipe RH.</p>
        <div>
          <label class="mb-1 block text-xs font-semibold text-ink-2">Sujet (optionnel)</label>
          <input
            v-model="rhSujet"
            maxlength="200"
            placeholder="Ex. Besoin de renfort · Retail Banking"
            class="w-full rounded-xl border border-border bg-panel px-3 py-2 text-sm outline-none focus:border-green-line"
          />
        </div>
        <div>
          <label class="mb-1 block text-xs font-semibold text-ink-2">Message</label>
          <textarea
            v-model="rhMessage"
            rows="4"
            maxlength="1000"
            placeholder="Votre message aux RH…"
            class="w-full rounded-xl border border-border bg-panel px-3 py-2 text-sm outline-none focus:border-green-line"
          />
        </div>
        <div class="flex justify-end gap-2">
          <BaseButton variant="secondary" size="sm" @click="showRhMsg = false">Annuler</BaseButton>
          <BaseButton size="sm" :disabled="!rhMessage.trim() || rhSending" @click="sendRh">
            {{ rhSending ? 'Envoi…' : 'Envoyer' }}
          </BaseButton>
        </div>
      </div>
    </BaseModal>
  </div>
</template>
