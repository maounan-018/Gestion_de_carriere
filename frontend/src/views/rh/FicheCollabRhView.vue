<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { apiService } from '@/services/apiService'
import { byPctDesc, scoreText, scoreBar } from '@/utils/score'
import { useToast } from '@/composables/useToast'
import type { RhPerson } from '@/types/rh'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseChip from '@/components/ui/BaseChip.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseAvatar from '@/components/ui/BaseAvatar.vue'
import BaseBreadcrumb from '@/components/ui/BaseBreadcrumb.vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

const route = useRoute()
const { toast } = useToast()
const p = ref<RhPerson | null>(null)
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    p.value = (await apiService.getRhPerson(route.params.id as string)) ?? null
  } catch {
    error.value = 'Impossible de charger la fiche.'
  } finally {
    loading.value = false
  }
}
onMounted(load)
watch(() => route.params.id, load)

// Édition RH du profil (PATCH /profils/{id} · réservé RH/ADMIN).
const showEdit = ref(false)
const saving = ref(false)
const editPoste = ref('')
const editAspi = ref('')
function openEdit() {
  if (!p.value) return
  editPoste.value = p.value.role === '—' ? '' : p.value.role
  editAspi.value = p.value.aspiration ?? ''
  showEdit.value = true
}
async function save() {
  if (!p.value || saving.value) return
  saving.value = true
  try {
    await apiService.updateProfil(p.value.id, {
      poste_actuel: editPoste.value.trim(),
      aspirations: editAspi.value.trim(),
    })
    showEdit.value = false
    toast('Profil mis à jour')
    await load()
  } catch (e) {
    toast(e instanceof Error ? e.message : 'Échec de la mise à jour', 'error')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <LoadingState v-if="loading" label="Chargement de la fiche…" />
  <ErrorState v-else-if="error" :message="error">
    <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
  </ErrorState>
  <EmptyState v-else-if="!p" title="Collaborateur introuvable" text="Cette fiche n'existe pas.">
    <template #action>
      <RouterLink :to="{ name: 'rh.annuaire' }"><BaseButton size="sm">Retour à l'annuaire</BaseButton></RouterLink>
    </template>
  </EmptyState>

  <div v-else>
    <BaseBreadcrumb :items="[{ label: 'Annuaire', to: { name: 'rh.annuaire' } }, { label: p.name }]" />

    <div class="grid gap-5 lg:grid-cols-[1fr_300px]">
      <div class="space-y-5">
        <BaseCard>
          <div class="flex flex-wrap items-center gap-4">
            <BaseAvatar :initials="p.initials" size="xl" />
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-center gap-2">
                <h2 class="font-display text-2xl font-bold text-ink">{{ p.name }}</h2>
                <BasePill v-if="p.flag === 'top'" tone="new">Haut potentiel</BasePill>
                <BasePill v-else-if="p.riskDeparture" tone="hot">Risque de départ</BasePill>
              </div>
              <p class="text-sm text-ink-3">{{ p.role }} · {{ p.pole }} · {{ p.seniority }}</p>
            </div>
            <div class="text-center">
              <div class="font-display text-2xl font-extrabold text-green-deep">{{ p.ring }}%</div>
              <div class="text-[10px] text-ink-3">profil</div>
            </div>
            <BaseButton variant="secondary" size="sm" @click="openEdit">
              <AppIcon name="user" :size="14" /> Éditer
            </BaseButton>
          </div>
        </BaseCard>

        <BaseCard title="Compétences">
          <div class="space-y-3">
            <div v-for="s in byPctDesc(p.skills)" :key="s.label">
              <div class="mb-1 flex justify-between text-xs">
                <span class="font-medium text-ink-2">{{ s.label }}</span>
                <span class="font-semibold" :class="scoreText(s.pct)">{{ s.pct }}%</span>
              </div>
              <div class="h-1.5 overflow-hidden rounded-full bg-panel-2">
                <div class="h-full rounded-full" :class="scoreBar(s.pct)" :style="{ width: s.pct + '%' }" />
              </div>
            </div>
          </div>
        </BaseCard>

        <div class="grid gap-5 sm:grid-cols-2">
          <BaseCard title="Points forts">
            <div class="flex flex-wrap gap-2"><BaseChip v-for="s in p.strengths" :key="s" tone="green">{{ s }}</BaseChip></div>
          </BaseCard>
          <BaseCard title="À développer">
            <div class="flex flex-wrap gap-2"><BaseChip v-for="g in p.gaps" :key="g" tone="gap">{{ g }}</BaseChip></div>
          </BaseCard>
        </div>
      </div>

      <div class="space-y-5">
        <BaseCard title="Aspiration">
          <div class="rounded-xl border border-green-line bg-green-ghost p-3">
            <div class="flex items-center gap-2 text-green-deep">
              <AppIcon name="route" :size="15" /><b class="text-sm">{{ p.aspiration }}</b>
            </div>
            <p class="mt-1 text-xs text-ink-2">Horizon {{ p.aspirationHorizon }}</p>
          </div>
        </BaseCard>
        <BaseCard title="CV du collaborateur">
          <a
            v-if="p.cvFilename"
            :href="apiService.cvUrl(Number(p.id))"
            target="_blank"
            rel="noopener"
            class="flex items-center gap-3 rounded-xl border border-green-line bg-green-ghost p-3 transition hover:bg-green-soft"
          >
            <div class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-green text-white"><AppIcon name="brief" :size="16" /></div>
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-bold text-green-deep">{{ p.cvFilename }}</p>
              <p class="text-xs text-ink-3">Ouvrir le CV (PDF)</p>
            </div>
          </a>
          <p v-else class="text-sm text-ink-3">Aucun CV déposé par ce collaborateur.</p>
        </BaseCard>
        <BaseCard title="Suivi HRBP">
          <div class="flex items-center justify-between text-sm">
            <span class="text-ink-3">Dernier entretien RH</span>
            <b :class="p.riskDeparture ? 'text-danger' : 'text-ink'">{{ p.lastRh }}</b>
          </div>
          <RouterLink :to="{ name: 'rh.bilan', params: { id: p.id } }" class="mt-3 block">
            <BaseButton block><AppIcon name="chat" :size="15" /> Préparer un entretien</BaseButton>
          </RouterLink>
        </BaseCard>
      </div>
    </div>

    <!-- Édition RH du profil -->
    <BaseModal v-model="showEdit" :title="`Éditer · ${p.name}`">
      <div class="space-y-4">
        <div>
          <label for="edit-poste" class="mb-1.5 block text-xs font-semibold text-ink-2">Poste actuel</label>
          <input
            id="edit-poste"
            v-model="editPoste"
            placeholder="Ex : Conseiller clientèle particuliers"
            class="w-full rounded-xl border border-border bg-paper px-3 py-2 text-sm outline-none focus:border-green-line"
          />
        </div>
        <div>
          <label for="edit-aspi" class="mb-1.5 block text-xs font-semibold text-ink-2">Aspiration / poste visé</label>
          <textarea
            id="edit-aspi"
            v-model="editAspi"
            rows="3"
            placeholder="Ex : Chargé d'affaires professionnels"
            class="w-full rounded-xl border border-border bg-paper px-3 py-2 text-sm outline-none focus:border-green-line"
          />
        </div>
      </div>
      <template #footer>
        <BaseButton variant="secondary" size="sm" @click="showEdit = false">Annuler</BaseButton>
        <BaseButton size="sm" :disabled="saving" @click="save">
          <AppIcon name="check" :size="14" /> {{ saving ? 'Enregistrement…' : 'Enregistrer' }}
        </BaseButton>
      </template>
    </BaseModal>
  </div>
</template>
