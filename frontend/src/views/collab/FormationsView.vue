<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import { useSessionStore } from '@/stores/session'
import type { Formation, FormationStatus } from '@/types/domain'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseChip from '@/components/ui/BaseChip.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

const items = ref<Formation[]>([])
const loading = ref(true)
const error = ref('')
const { toast } = useToast()
const session = useSessionStore()

/* ---- Attestation (formation terminée) ---- */
const attFormation = ref<Formation | null>(null)
const showAtt = computed({
  get: () => attFormation.value !== null,
  set: (v: boolean) => { if (!v) attFormation.value = null },
})
const today = new Date().toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })
function openAttestation(f: Formation) {
  attFormation.value = f
}

/* ---- Détail + inscription ---- */
const detail = ref<Formation | null>(null)
const showDetail = computed({
  get: () => detail.value !== null,
  set: (v: boolean) => { if (!v) detail.value = null },
})
function openDetail(f: Formation) {
  detail.value = f
}
/** Description composée (le catalogue backend n'a pas de champ description dédié). */
function descriptionOf(f: Formation): string {
  const bits: string[] = []
  const niv = f.level ? f.level.toLowerCase() : ''
  bits.push(`Formation ${niv ? niv + ' ' : ''}proposée par ${f.provider || 'BMCI Academy'}, d'une durée de ${f.duration || '—'}.`)
  if (f.reason) bits.push(f.reason.replace('Compétence visée', 'Elle vise le développement de la compétence') + '.')
  if (f.tags.length) bits.push('Thèmes abordés : ' + f.tags.join(', ') + '.')
  return bits.join(' ')
}
/** Inscription : le backend n'a pas de suivi LMS → bascule locale en « en cours ». */
function enroll(f: Formation) {
  if (f.status === 'in-progress') {
    toast('Reprise de la formation…')
  } else {
    f.status = 'in-progress'
    f.progress = 5
    toast('Inscription enregistrée · formation ajoutée à « En cours »', 'ok')
  }
  detail.value = null
}

const filters = [
  { key: 'all', label: 'Toutes' },
  { key: 'in-progress', label: 'En cours' },
  { key: 'recommended', label: 'Recommandées' },
  { key: 'done', label: 'Terminées' },
] as const
const active = ref<'all' | FormationStatus>('all')

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = await apiService.getFormations()
  } catch {
    error.value = 'Impossible de charger les formations.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

const query = ref('')
const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  return items.value.filter((f) => {
    const okStatus = active.value === 'all' || f.status === active.value
    const okQuery = !q
      || (`${f.title} ${f.provider} ${f.level} ${f.reason ?? ''} ${f.tags.join(' ')}`)
        .toLowerCase().includes(q)
    return okStatus && okQuery
  })
})

const STATUS: Record<FormationStatus, { label: string; tone: 'new' | 'ai' | 'ok' }> = {
  'recommended': { label: 'Recommandée', tone: 'ai' },
  'in-progress': { label: 'En cours', tone: 'new' },
  'done': { label: 'Terminée', tone: 'ok' },
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center gap-2 rounded-xl border border-border bg-paper px-3 py-2">
      <AppIcon name="search" :size="16" class="shrink-0 text-ink-3" />
      <input
        v-model="query"
        type="search"
        placeholder="Rechercher un cours : compétence, thème, domaine…"
        class="w-full bg-transparent text-sm outline-none placeholder:text-ink-3"
      />
    </div>
    <div class="flex flex-wrap gap-2">
      <button
        v-for="f in filters"
        :key="f.key"
        class="rounded-full border px-3 py-1 text-xs font-semibold transition"
        :class="active === f.key ? 'border-green bg-green text-white' : 'border-border bg-paper text-ink-2 hover:border-green-line hover:text-green-deep'"
        @click="active = f.key"
      >{{ f.label }}</button>
    </div>

    <LoadingState v-if="loading" label="Chargement des formations…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>
    <EmptyState v-else-if="filtered.length === 0" title="Aucune formation" text="Aucune formation dans cette catégorie pour le moment." />

    <div v-else class="grid gap-4 sm:grid-cols-2">
      <div
        v-for="f in filtered"
        :key="f.id"
        class="flex cursor-pointer flex-col rounded-2xl border border-border bg-paper p-4 shadow-card transition hover:-translate-y-0.5 hover:border-green-line hover:shadow-float"
        @click="openDetail(f)"
      >
        <div class="flex items-start justify-between gap-2">
          <div class="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-green-soft text-green-deep"><AppIcon name="book" :size="18" /></div>
          <BasePill :tone="STATUS[f.status].tone">{{ STATUS[f.status].label }}</BasePill>
        </div>
        <h4 class="mt-2.5 text-sm font-bold text-ink">{{ f.title }}</h4>
        <p class="text-xs text-ink-3">{{ f.provider }}</p>
        <div class="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-ink-3">
          <span class="inline-flex items-center gap-1"><AppIcon name="clock" :size="11" /> {{ f.duration }}</span>
          <span class="inline-flex items-center gap-1"><AppIcon name="spark" :size="11" /> {{ f.level }}</span>
        </div>
        <div class="mt-2 flex flex-wrap gap-1.5">
          <BaseChip v-for="t in f.tags" :key="t">{{ t }}</BaseChip>
        </div>
        <p v-if="f.reason" class="mt-2 text-xs text-green-deep"><AppIcon name="spark" :size="12" class="inline" /> {{ f.reason }}</p>

        <div v-if="f.status === 'in-progress'" class="mt-3">
          <div class="mb-1 flex justify-between text-xs"><span class="text-ink-3">Avancement</span><b class="text-green-deep">{{ f.progress }} %</b></div>
          <div class="h-2 overflow-hidden rounded-full bg-panel-2"><div class="h-full rounded-full bg-green" :style="{ width: f.progress + '%' }" /></div>
        </div>

        <div class="mt-3 flex-1" />
        <div class="mt-2">
          <BaseButton
            v-if="f.status === 'done'"
            variant="secondary" size="sm" block
            @click.stop="openAttestation(f)"
          ><AppIcon name="award" :size="14" /> Voir l'attestation</BaseButton>
          <BaseButton
            v-else size="sm" block
            @click.stop="enroll(f)"
          >{{ f.status === 'in-progress' ? 'Reprendre' : "S'inscrire" }}</BaseButton>
        </div>
      </div>
    </div>

    <BaseModal v-model="showDetail" :title="detail?.title || 'Formation'">
      <div v-if="detail" class="space-y-4">
        <div class="flex flex-wrap items-center gap-2">
          <BasePill :tone="STATUS[detail.status].tone">{{ STATUS[detail.status].label }}</BasePill>
          <span class="inline-flex items-center gap-1 text-xs text-ink-3"><AppIcon name="clock" :size="12" /> {{ detail.duration }}</span>
          <span class="inline-flex items-center gap-1 text-xs text-ink-3"><AppIcon name="spark" :size="12" /> {{ detail.level }}</span>
        </div>
        <p class="text-sm leading-relaxed text-ink-2">{{ descriptionOf(detail) }}</p>
        <div v-if="detail.tags.length" class="flex flex-wrap gap-1.5">
          <BaseChip v-for="t in detail.tags" :key="t">{{ t }}</BaseChip>
        </div>
        <div v-if="detail.status === 'in-progress'">
          <div class="mb-1 flex justify-between text-xs"><span class="text-ink-3">Avancement</span><b class="text-green-deep">{{ detail.progress }} %</b></div>
          <div class="h-2 overflow-hidden rounded-full bg-panel-2"><div class="h-full rounded-full bg-green" :style="{ width: detail.progress + '%' }" /></div>
        </div>
      </div>
      <template #footer>
        <BaseButton variant="secondary" size="sm" @click="showDetail = false">Fermer</BaseButton>
        <BaseButton
          v-if="detail && detail.status === 'done'"
          size="sm"
          @click="() => { const f = detail!; showDetail = false; openAttestation(f) }"
        ><AppIcon name="award" :size="14" /> Voir l'attestation</BaseButton>
        <BaseButton v-else-if="detail" size="sm" @click="enroll(detail)">
          {{ detail.status === 'in-progress' ? 'Reprendre' : "S'inscrire" }}
        </BaseButton>
      </template>
    </BaseModal>

    <BaseModal v-model="showAtt" title="Attestation de formation">
      <div v-if="attFormation" class="rounded-2xl border border-green-line bg-green-ghost p-6 text-center">
        <div class="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-full bg-green text-white">
          <AppIcon name="award" :size="24" />
        </div>
        <p class="text-xs font-semibold uppercase tracking-wide text-green-deep">Attestation de réussite</p>
        <h3 class="mt-2 font-display text-lg font-bold text-ink">{{ attFormation.title }}</h3>
        <p class="mt-1 text-sm text-ink-2">{{ attFormation.provider }} · {{ attFormation.duration }}</p>
        <div class="my-4 h-px bg-green-line" />
        <p class="text-sm text-ink-2">
          Délivrée à <b class="text-ink">{{ session.user?.name || 'Collaborateur' }}</b>
          <span v-if="session.user?.title"> · {{ session.user.title }}</span>
        </p>
        <p class="mt-1 text-xs text-ink-3">Formation suivie avec succès · le {{ today }}</p>
        <p class="mt-4 text-[11px] italic text-ink-3">Document de démonstration · sans valeur officielle.</p>
      </div>
      <template #footer>
        <BaseButton size="sm" @click="showAtt = false">Fermer</BaseButton>
      </template>
    </BaseModal>
  </div>
</template>
