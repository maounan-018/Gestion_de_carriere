<script setup lang="ts">
/**
 * Publier une offre · composant PARTAGÉ (RH & manager).
 * Sélecteur de FICHE DE POSTE : on choisit un poste → sa fiche (mission,
 * compétences attendues) se charge et sert de référence (compétences héritées
 * comme critères de matching). Champs : type, intitulé, localisation, durée,
 * description. L'offre est créée en brouillon via POST /offres.
 */
import { ref, computed, watch } from 'vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { FicheListItem, FicheDetail } from '@/types/rh'
import BaseModal from '@/components/ui/BaseModal.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseChip from '@/components/ui/BaseChip.vue'
import AppIcon from '@/components/ui/AppIcon.vue'

// `allowPoste` (défaut true) : la RH publie tous les types ; le manager ne publie
// que missions/projets (les POSTES relèvent de la RH · règle backend).
const props = withDefaults(defineProps<{ modelValue: boolean; allowPoste?: boolean }>(), {
  allowPoste: true,
})
const emit = defineEmits<{ 'update:modelValue': [boolean]; published: [] }>()
const { toast } = useToast()

const ALL_TYPES = ['Poste', 'Mission transverse', 'Projet'] as const
type OffreType = (typeof ALL_TYPES)[number]
const types = computed<readonly OffreType[]>(() =>
  props.allowPoste ? ALL_TYPES : ['Mission transverse', 'Projet'],
)
const inputCls =
  'w-full rounded-xl border border-border bg-panel px-3 py-2 text-sm text-ink outline-none focus:border-green-line'

const type = ref<OffreType>(props.allowPoste ? 'Poste' : 'Mission transverse')
const titre = ref('')
const description = ref('')
const localisation = ref('')
const duree = ref('')
const publishing = ref(false)

// Sélecteur de fiche de poste : menu déroulant des intitulés → chargement de la fiche.
const fichesList = ref<FicheListItem[]>([])
const ficheId = ref<number | null>(null)
const fiche = ref<FicheDetail | null>(null)

// Compétences canoniques ATTENDUES, déclarées par le manager (retour tuteur : une
// mission/un projet doit déclarer les compétences exigées des candidats). Ancrées
// au référentiel via l'autocomplétion (skill_id) ; saisie libre possible en repli.
type ExpectedComp = { libelle: string; skill_id: number | null; importance: 'essentielle' | 'souhaitee' }
const competences = ref<ExpectedComp[]>([])
const compSearch = ref('')
const compResults = ref<{ skill_id: number; label: string }[]>([])
let compTimer: ReturnType<typeof setTimeout> | null = null

function onCompSearch() {
  if (compTimer) clearTimeout(compTimer)
  const q = compSearch.value.trim()
  if (q.length < 2) {
    compResults.value = []
    return
  }
  compTimer = setTimeout(async () => {
    try {
      compResults.value = await apiService.rechercherCompetences(q)
    } catch {
      compResults.value = []
    }
  }, 250)
}
function addComp(c: { skill_id: number | null; label: string }) {
  const label = c.label.trim()
  if (!label || competences.value.some((x) => x.libelle.toLowerCase() === label.toLowerCase())) return
  competences.value.push({ libelle: label, skill_id: c.skill_id, importance: 'essentielle' })
  compSearch.value = ''
  compResults.value = []
}
function addFreeComp() {
  if (compSearch.value.trim().length >= 2) addComp({ skill_id: null, label: compSearch.value.trim() })
}
function removeComp(i: number) {
  competences.value.splice(i, 1)
}
function toggleImportance(c: ExpectedComp) {
  c.importance = c.importance === 'essentielle' ? 'souhaitee' : 'essentielle'
}

function reset() {
  type.value = props.allowPoste ? 'Poste' : 'Mission transverse'
  titre.value = ''
  description.value = ''
  localisation.value = ''
  duree.value = ''
  ficheId.value = null
  fiche.value = null
  competences.value = []
  compSearch.value = ''
  compResults.value = []
}
watch(
  () => props.modelValue,
  async (open) => {
    if (!open) return
    reset()
    try {
      fichesList.value = await apiService.getFiches()   // toutes les fiches → menu déroulant
    } catch {
      fichesList.value = []
    }
  },
)

// Sélection d'un poste dans le menu déroulant → charge sa fiche (mission, compétences…).
async function onFicheChange() {
  fiche.value = null
  if (ficheId.value == null) return
  const f = fichesList.value.find((x) => x.id === ficheId.value)
  if (f) titre.value = f.intitule_poste
  try {
    fiche.value = await apiService.getFiche(ficheId.value)
  } catch {
    fiche.value = null
  }
}

function clearFiche() {
  ficheId.value = null
  fiche.value = null
}

async function publish() {
  if (publishing.value || !titre.value.trim()) return
  // Compétences attendues obligatoires : héritées d'une fiche OU déclarées ici.
  const heritees = fiche.value?.competences.length ?? 0
  if (competences.value.length === 0 && heritees === 0) {
    toast('Déclarez au moins une compétence attendue pour les candidats.', 'error')
    return
  }
  publishing.value = true
  try {
    await apiService.publishOffer({
      titre: titre.value.trim(),
      type: type.value,
      ficheId: ficheId.value,
      description: description.value.trim(),
      localisation: localisation.value.trim(),
      duree: duree.value.trim(),
      competences: competences.value,
    })
    toast('Offre créée en brouillon', 'ok')
    emit('published')
    emit('update:modelValue', false)
  } catch (e) {
    toast(e instanceof Error ? e.message : 'Échec de la publication', 'error')
  } finally {
    publishing.value = false
  }
}
</script>

<template>
  <BaseModal
    :model-value="modelValue"
    title="Publier une offre"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="space-y-4">
      <!-- Type -->
      <div>
        <label class="mb-1.5 block text-xs font-semibold text-ink-2">Type</label>
        <div class="flex flex-wrap gap-1.5">
          <button
            v-for="t in types"
            :key="t"
            type="button"
            class="flex-1 rounded-lg border px-2 py-1.5 text-xs font-semibold transition"
            :class="type === t ? 'border-green bg-green text-white' : 'border-border bg-paper text-ink-2 hover:text-ink'"
            @click="type = t"
          >
            {{ t }}
          </button>
        </div>
      </div>

      <!-- Sélecteur de fiche de poste -->
      <div>
        <label class="mb-1.5 block text-xs font-semibold text-ink-2">Fiche de poste (référence)</label>
        <select v-model="ficheId" :class="inputCls" @change="onFicheChange">
          <option :value="null">Choisir un poste…</option>
          <option v-for="f in fichesList" :key="f.id" :value="f.id">{{ f.intitule_poste }}</option>
        </select>
        <p v-if="!ficheId" class="mt-1 text-[11px] text-ink-3">
          Sélectionnez un poste pour charger sa fiche, ou saisissez un intitulé libre ci-dessous.
        </p>
      </div>

      <!-- Aperçu de la fiche choisie -->
      <div v-if="fiche" class="rounded-xl border border-green-line bg-green-ghost p-3">
        <div class="flex items-center justify-between">
          <h4 class="text-sm font-bold text-green-deep">{{ fiche.intitule_poste }}</h4>
          <button type="button" class="text-xs font-semibold text-ink-3 hover:underline" @click="clearFiche">
            Retirer
          </button>
        </div>
        <p v-if="fiche.mission" class="mt-1 line-clamp-3 text-xs text-ink-2">{{ fiche.mission }}</p>
        <div v-if="fiche.competences.length" class="mt-2 flex flex-wrap gap-1">
          <BaseChip v-for="(c, i) in fiche.competences.slice(0, 8)" :key="i">{{ c.libelle }}</BaseChip>
        </div>
        <p class="mt-2 text-[11px] text-green-deep">
          Les compétences attendues seront héritées comme critères de matching.
        </p>
      </div>

      <!-- Compétences canoniques ATTENDUES (déclarées par le manager) -->
      <div>
        <label class="mb-1.5 block text-xs font-semibold text-ink-2">
          Compétences attendues <span class="text-danger">*</span>
        </label>
        <p class="mb-1.5 text-[11px] text-ink-3">
          Déclarez les compétences canoniques exigées des candidats (référentiel ESCO · O*NET · SFIA) —
          elles servent au matching. <span v-if="fiche">Celles de la fiche sont déjà héritées ; ajoutez-en si besoin.</span>
        </p>
        <div class="relative">
          <input
            v-model="compSearch"
            :class="inputCls"
            placeholder="Rechercher une compétence… (ex : gestion des risques)"
            @input="onCompSearch"
            @keydown.enter.prevent="addFreeComp"
          />
          <div
            v-if="compResults.length"
            class="absolute z-10 mt-1 max-h-56 w-full overflow-auto rounded-xl border border-border bg-paper shadow-float"
          >
            <button
              v-for="r in compResults"
              :key="r.skill_id"
              type="button"
              class="block w-full px-3 py-2 text-left text-sm hover:bg-green-ghost"
              @click="addComp(r)"
            >
              <span class="font-semibold text-ink">{{ r.label }}</span>
              <span class="ml-1 text-[11px] text-green-deep">· canonique</span>
            </button>
          </div>
        </div>
        <div v-if="competences.length" class="mt-2 flex flex-wrap gap-1.5">
          <span
            v-for="(c, i) in competences"
            :key="i"
            class="inline-flex items-center gap-1.5 rounded-full border border-green-line bg-green-ghost py-1 pl-2.5 pr-1.5 text-xs"
          >
            <button
              type="button"
              class="font-semibold"
              :class="c.importance === 'essentielle' ? 'text-green-deep' : 'text-ink-2'"
              :title="c.skill_id ? 'Compétence canonique (référentiel) · cliquez pour l’importance' : 'Compétence libre · cliquez pour l’importance'"
              @click="toggleImportance(c)"
            >
              {{ c.libelle }} · {{ c.importance === 'essentielle' ? 'essentielle' : 'souhaitée' }}
            </button>
            <button type="button" class="text-ink-3 hover:text-danger" aria-label="Retirer" @click="removeComp(i)">×</button>
          </span>
        </div>
      </div>

      <!-- Intitulé -->
      <div>
        <label class="mb-1.5 block text-xs font-semibold text-ink-2">Intitulé de l'offre</label>
        <input v-model="titre" :class="inputCls" maxlength="200" placeholder="Ex : Responsable Conformité" />
      </div>

      <!-- Localisation + Durée -->
      <div class="grid gap-3 sm:grid-cols-2">
        <div>
          <label class="mb-1.5 block text-xs font-semibold text-ink-2">Localisation</label>
          <input v-model="localisation" :class="inputCls" maxlength="120" placeholder="Ex : Casablanca · Siège" />
        </div>
        <div>
          <label class="mb-1.5 block text-xs font-semibold text-ink-2">Durée</label>
          <input v-model="duree" :class="inputCls" maxlength="64" placeholder="Ex : CDI · ou 6 mois (mission)" />
        </div>
      </div>

      <!-- Description / précisions -->
      <div>
        <label class="mb-1.5 block text-xs font-semibold text-ink-2">Description / précisions</label>
        <textarea
          v-model="description"
          rows="4"
          :class="inputCls"
          placeholder="Contexte, missions, précisions sur le poste / projet…"
        />
      </div>

      <div class="flex items-start gap-2 rounded-xl border border-green-line bg-green-ghost px-3 py-2 text-xs text-green-deep">
        <AppIcon name="shield" :size="14" />
        <span>L'offre est créée en <b>brouillon</b> ; vous la publierez depuis la liste.</span>
      </div>
    </div>
    <template #footer>
      <BaseButton variant="secondary" size="sm" @click="emit('update:modelValue', false)">Annuler</BaseButton>
      <BaseButton size="sm" :disabled="!titre.trim() || publishing" @click="publish">
        <AppIcon name="send" :size="14" /> {{ publishing ? 'Publication…' : 'Publier' }}
      </BaseButton>
    </template>
  </BaseModal>
</template>
