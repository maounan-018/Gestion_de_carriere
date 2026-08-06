<script setup lang="ts">
/**
 * Évaluation de MISSION (post-clôture) — Workstream C. Le manager voit son offre
 * et les participants RETENUS ; il note (1-10) les compétences réellement UTILISÉES
 * dans la mission. Une compétence notée absente du profil y est AJOUTÉE, attribuée
 * à son évaluation (« évaluée par X dans le cadre de la mission Y »). Les compétences
 * non utilisées ne sont pas notées.
 */
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, Check, Search } from '@lucide/vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseAvatar from '@/components/ui/BaseAvatar.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const route = useRoute()
const { toast } = useToast()

type Ctx = Awaited<ReturnType<typeof apiService.getMissionEvalContext>>
type Row = { libelle: string; skill_id: number | null; score: number } // score 0 = non utilisée

const offreId = route.params.key as string
const ctx = ref<Ctx | null>(null)
const loading = ref(true)
const error = ref('')
const forms = ref<Record<number, Row[]>>({}) // profil_id → lignes de compétences
const saving = ref<Record<number, boolean>>({})
const done = ref<Record<number, boolean>>({})
const addSearch = ref<Record<number, string>>({})
const addResults = ref<Record<number, { skill_id: number; label: string }[]>>({})
let addTimer: ReturnType<typeof setTimeout> | null = null

function initials(nom: string): string {
  const p = nom.trim().split(/\s+/)
  return ((p[0]?.[0] ?? '') + (p[1]?.[0] ?? '')).toUpperCase()
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const c = await apiService.getMissionEvalContext(offreId)
    ctx.value = c
    const f: Record<number, Row[]> = {}
    for (const p of c.participants) {
      f[p.profil_id] = c.competences.map((k) => ({ libelle: k.libelle, skill_id: k.skill_id, score: 0 }))
    }
    forms.value = f
  } catch {
    error.value = "Impossible de charger l'évaluation de mission."
  } finally {
    loading.value = false
  }
}
onMounted(load)

function onAddSearch(pid: number) {
  if (addTimer) clearTimeout(addTimer)
  const q = (addSearch.value[pid] || '').trim()
  if (q.length < 2) {
    addResults.value[pid] = []
    return
  }
  addTimer = setTimeout(async () => {
    try {
      addResults.value[pid] = await apiService.rechercherCompetences(q)
    } catch {
      addResults.value[pid] = []
    }
  }, 250)
}
function addRow(pid: number, c: { skill_id: number | null; label: string }) {
  const rows = forms.value[pid]
  if (rows.some((r) => r.libelle.toLowerCase() === c.label.toLowerCase())) return
  rows.push({ libelle: c.label, skill_id: c.skill_id, score: 0 })
  addSearch.value[pid] = ''
  addResults.value[pid] = []
}
function addFree(pid: number) {
  const q = (addSearch.value[pid] || '').trim()
  if (q.length >= 2) addRow(pid, { skill_id: null, label: q })
}

async function valider(pid: number) {
  if (saving.value[pid]) return
  const rows = (forms.value[pid] || []).filter((r) => r.score > 0)
  if (!rows.length) {
    toast('Notez au moins une compétence utilisée (1-10).', 'error')
    return
  }
  saving.value[pid] = true
  try {
    const res = await apiService.evaluerParticipantMission(
      offreId, pid,
      rows.map((r) => ({ libelle: r.libelle, skill_id: r.skill_id, score: r.score })),
    )
    const nom = ctx.value?.participants.find((p) => p.profil_id === pid)?.nom || 'le participant'
    toast(
      `${res.evaluees} compétence(s) évaluée(s)${res.ajoutees ? ` · ${res.ajoutees} ajoutée(s) au profil de ${nom}` : ''}.`,
      'ok',
    )
    done.value[pid] = true
  } catch (e) {
    toast(e instanceof Error ? e.message : "Échec de l'évaluation.", 'error')
  } finally {
    saving.value[pid] = false
  }
}
</script>

<template>
  <div class="space-y-5">
    <RouterLink
      :to="{ name: 'manager.offres' }"
      class="inline-flex items-center gap-1.5 text-sm font-semibold text-green-deep hover:underline"
    >
      <ArrowLeft :size="15" /> Retour aux offres
    </RouterLink>

    <LoadingState v-if="loading" label="Chargement de l'évaluation de mission…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>

    <template v-else-if="ctx">
      <div>
        <div class="text-xs font-semibold uppercase tracking-wide text-green-deep">Évaluation de mission</div>
        <h2 class="font-display text-2xl font-bold text-ink">{{ ctx.titre }}</h2>
        <p class="max-w-2xl text-sm text-ink-3">
          Notez de 1 à 10 les compétences réellement <b>utilisées</b> par chaque participant.
          Laissez « non utilisée » sinon. Une compétence notée absente du profil y sera ajoutée,
          attribuée à votre évaluation.
        </p>
      </div>

      <EmptyState
        v-if="!ctx.participants.length"
        title="Aucun participant retenu"
        text="Retenez des candidats sur cette offre (revue des candidatures), puis clôturez-la, pour évaluer leurs compétences."
      />

      <BaseCard v-for="p in ctx.participants" :key="p.profil_id">
        <template #header>
          <div class="flex items-center gap-3">
            <BaseAvatar :initials="initials(p.nom)" :seed="String(p.profil_id)" size="md" />
            <div class="min-w-0 flex-1">
              <h3 class="font-display text-base font-bold text-ink">{{ p.nom }}</h3>
              <p class="truncate text-xs text-ink-3">{{ p.poste_actuel || '—' }}</p>
            </div>
            <BasePill v-if="done[p.profil_id]" tone="new"><Check :size="12" /> évalué</BasePill>
          </div>
        </template>

        <div class="space-y-2">
          <div v-for="(r, i) in forms[p.profil_id]" :key="i" class="flex items-center gap-3">
            <span class="min-w-0 flex-1 truncate text-sm text-ink-2">{{ r.libelle }}</span>
            <select
              v-model.number="r.score"
              class="shrink-0 rounded-lg border border-border bg-panel px-2 py-1 text-sm text-ink outline-none focus:border-green-line"
            >
              <option :value="0">Non utilisée</option>
              <option v-for="n in 10" :key="n" :value="n">{{ n }}/10</option>
            </select>
          </div>
          <p v-if="!forms[p.profil_id]?.length" class="text-xs text-ink-3">
            Aucune compétence attendue déclarée sur l'offre — ajoutez celles utilisées ci-dessous.
          </p>
        </div>

        <!-- Ajouter une compétence utilisée hors attendus -->
        <div class="relative mt-3">
          <div class="flex items-center gap-2 rounded-lg border border-border bg-panel px-2 focus-within:border-green-line">
            <Search :size="14" class="shrink-0 text-ink-3" />
            <input
              v-model="addSearch[p.profil_id]"
              placeholder="Ajouter une compétence utilisée (hors attendus)…"
              class="w-full bg-transparent py-1.5 text-sm text-ink outline-none"
              @input="onAddSearch(p.profil_id)"
              @keydown.enter.prevent="addFree(p.profil_id)"
            />
          </div>
          <div
            v-if="addResults[p.profil_id]?.length"
            class="absolute z-10 mt-1 max-h-48 w-full overflow-auto rounded-xl border border-border bg-paper shadow-float"
          >
            <button
              v-for="rr in addResults[p.profil_id]"
              :key="rr.skill_id"
              type="button"
              class="block w-full px-3 py-2 text-left text-sm hover:bg-green-ghost"
              @click="addRow(p.profil_id, rr)"
            >
              <span class="font-semibold text-ink">{{ rr.label }}</span>
              <span class="ml-1 text-[11px] text-green-deep">· canonique</span>
            </button>
          </div>
        </div>

        <div class="mt-4 flex justify-end">
          <BaseButton size="sm" :disabled="saving[p.profil_id]" @click="valider(p.profil_id)">
            <Check :size="14" />
            {{ saving[p.profil_id] ? 'Enregistrement…' : (done[p.profil_id] ? 'Mettre à jour' : "Valider l'évaluation") }}
          </BaseButton>
        </div>
      </BaseCard>
    </template>
  </div>
</template>
