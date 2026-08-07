<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { BookOpen } from '@lucide/vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { CartoDoc, FicheGeneree } from '@/types/referentiel'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseBreadcrumb from '@/components/ui/BaseBreadcrumb.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const { toast } = useToast()

const inputCls =
  'w-full rounded-lg border border-border bg-paper px-2.5 py-1.5 text-sm outline-none focus:border-green-line'

// Référentiels ouverts mobilisés (attribution légale · statique, informatif).
const referentiels = [
  { code: 'ESCO', name: 'Skills, Competences & Occupations', role: 'Compétences & métiers', licence: 'CC BY 4.0' },
  { code: 'O*NET', name: 'Occupational Information Network', role: 'Aptitudes & activités', licence: 'CC BY 4.0' },
  { code: 'SFIA', name: 'Skills Framework for the Information Age', role: 'Niveaux 1→7', licence: 'Licence SFIA' },
]

// ---- État -----------------------------------------------------------------
const loading = ref(true)
const loadError = ref('')

interface DeptEdit { key: string; nom: string; pole: string; metiersText: string }
const depts = ref<DeptEdit[]>([])
const cartoVersion = ref<number | null>(null)
const cartoError = ref('')
const cartoBusy = ref(false)

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const c = await apiService.getCartographie()
    cartoVersion.value = c.version ?? null
    depts.value = c.departements.map((d) => ({
      key: d.key, nom: d.nom, pole: d.pole ?? '', metiersText: (d.metiers ?? []).join('\n'),
    }))
  } catch {
    loadError.value = 'Impossible de charger les référentiels.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

// ---- Cartographie ---------------------------------------------------------
function addDept() {
  depts.value.push({ key: '', nom: '', pole: '', metiersText: '' })
}
function removeDept(i: number) {
  depts.value.splice(i, 1)
}
async function saveCarto() {
  cartoError.value = ''
  cartoBusy.value = true
  try {
    const doc: CartoDoc = {
      version: cartoVersion.value,
      departements: depts.value.map((d) => ({
        key: d.key.trim(),
        nom: d.nom.trim(),
        pole: d.pole.trim() || null,
        metiers: d.metiersText.split('\n').map((m) => m.trim()).filter(Boolean),
      })),
    }
    const saved = await apiService.saveCartographie(doc)
    cartoVersion.value = saved.version ?? cartoVersion.value
    toast('Cartographie enregistrée', 'ok')
  } catch (e) {
    cartoError.value = (e as Error)?.message || 'Enregistrement refusé.'
  } finally {
    cartoBusy.value = false
  }
}

// ---- Génération de fiche de poste (IA) ------------------------------------
const genMetier = ref('')
const genDept = ref('')
const genBusy = ref(false)
const genError = ref('')
const genResult = ref<FicheGeneree | null>(null)
// Postes proposés = métiers du département choisi (sélection, plus de saisie libre).
const genMetiers = computed<string[]>(() => {
  const d = depts.value.find((x) => x.key === genDept.value)
  return d ? d.metiersText.split('\n').map((m) => m.trim()).filter(Boolean) : []
})
async function genererFiche() {
  const metier = genMetier.value.trim()
  if (!metier || !genDept.value || genBusy.value) return
  genBusy.value = true
  genError.value = ''
  genResult.value = null
  try {
    genResult.value = await apiService.genererFiche({ metier, departementKey: genDept.value })
    toast('Fiche générée', 'ok')
  } catch (e) {
    genError.value = (e as Error)?.message || 'Génération indisponible (IA). Réessayez.'
  } finally {
    genBusy.value = false
  }
}
</script>

<template>
  <div>
    <BaseBreadcrumb
      :items="[{ label: 'Supervision', to: { name: 'rh.supervision' } }, { label: 'Référentiel & fiches' }]"
    />

    <BaseCard class="mb-4">
      <div class="flex items-center gap-3">
        <div class="grid h-10 w-10 place-items-center rounded-xl bg-green-soft text-green-deep">
          <BookOpen :size="18" />
        </div>
        <div class="min-w-0">
          <h1 class="font-display text-lg font-bold text-ink">Référentiel & fiches de poste</h1>
          <p class="text-sm text-ink-3">
            Générez une fiche de poste (IA) pour un poste d'un département, et gérez la cartographie
            départements → métiers. Réservé RH/Admin ; chaque enregistrement est validé côté serveur.
          </p>
        </div>
      </div>
    </BaseCard>

    <h2 class="mb-2 font-display text-sm font-bold text-ink">Référentiels ouverts mobilisés</h2>
    <div class="mb-5 grid gap-3 sm:grid-cols-3">
      <BaseCard v-for="r in referentiels" :key="r.code" class="min-w-0">
        <div class="flex items-center gap-2">
          <h3 class="font-display text-base font-bold text-ink">{{ r.code }}</h3>
          <BasePill tone="ok">source ouverte</BasePill>
        </div>
        <p class="mt-0.5 text-xs text-ink-3">{{ r.name }}</p>
        <div class="mt-2 space-y-1 text-xs text-ink-2">
          <div><b class="text-ink-3">Apporte :</b> {{ r.role }}</div>
          <div><b class="text-ink-3">Licence :</b> {{ r.licence }}</div>
        </div>
      </BaseCard>
    </div>

    <LoadingState v-if="loading" label="Chargement des référentiels…" />
    <ErrorState v-else-if="loadError" :message="loadError">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>

    <div v-else class="space-y-5">
      <!-- Génération de fiche (IA) -->
      <BaseCard title="Générer une fiche de poste (IA)">
        <p class="mb-3 text-xs text-ink-3">
          L'IA rédige une fiche synthétique pour un métier d'un département (compétences inférées du
          graphe ESCO/O*NET/SFIA). Contenu de démonstration · jamais de données réelles.
        </p>
        <div class="grid gap-2 sm:grid-cols-[1fr_1fr_auto]">
          <select v-model="genDept" :class="inputCls" aria-label="Département" @change="genMetier = ''">
            <option value="" disabled>Département…</option>
            <option v-for="d in depts" :key="d.key" :value="d.key">{{ d.nom || d.key }}</option>
          </select>
          <select v-model="genMetier" :class="inputCls" aria-label="Poste" :disabled="!genDept">
            <option value="" disabled>{{ genDept ? 'Poste…' : 'Choisir un département d’abord' }}</option>
            <option v-for="m in genMetiers" :key="m" :value="m">{{ m }}</option>
          </select>
          <BaseButton :disabled="genBusy || !genMetier.trim() || !genDept" @click="genererFiche">
            <AppIcon name="spark" :size="15" /> {{ genBusy ? 'Génération…' : 'Générer' }}
          </BaseButton>
        </div>
        <p v-if="genError" class="mt-3 rounded-lg border border-warning/40 bg-warning-soft px-3 py-2 text-xs text-warning">
          {{ genError }}
        </p>

        <div v-if="genResult" class="mt-4 space-y-3 rounded-xl border border-green-line bg-green-ghost p-3">
          <div class="flex flex-wrap items-center gap-2">
            <h4 class="font-display text-sm font-bold text-ink">{{ genResult.metier }}</h4>
            <BasePill tone="mut">{{ genResult.departement }}</BasePill>
            <BasePill tone="ai">synthétique</BasePill>
          </div>
          <div v-for="(val, key) in genResult.sections" :key="key">
            <div class="text-[11px] font-semibold uppercase tracking-wide text-green-deep">{{ key }}</div>
            <p class="whitespace-pre-line text-sm text-ink-2">{{ val }}</p>
          </div>
          <div v-if="genResult.competences_reference.length">
            <div class="mb-1 text-[11px] font-semibold uppercase tracking-wide text-ink-3">
              Compétences de référence (graphe)
            </div>
            <div class="flex flex-wrap gap-1.5">
              <span
                v-for="c in genResult.competences_reference"
                :key="c"
                class="rounded-full border border-border bg-paper px-2 py-0.5 text-xs text-ink-2"
              >{{ c }}</span>
            </div>
          </div>
        </div>
      </BaseCard>

      <!-- Cartographie -->
      <BaseCard title="Cartographie départements → métiers">
        <template #actions>
          <BaseButton size="sm" variant="ghost" @click="addDept">+ Ajouter un département</BaseButton>
        </template>
        <p class="mb-3 text-xs text-ink-3">
          Chaque département : clé (unique), nom, pôle (optionnel), et la liste des métiers (un par ligne).
        </p>
        <div class="space-y-2">
          <div v-for="(d, i) in depts" :key="i" class="rounded-xl border border-border bg-panel p-2.5">
            <div class="grid gap-2 sm:grid-cols-[150px_1fr_1fr]">
              <input v-model="d.key" placeholder="clé" :class="inputCls" />
              <input v-model="d.nom" placeholder="Nom du département" :class="inputCls" />
              <input v-model="d.pole" placeholder="Pôle (optionnel)" :class="inputCls" />
            </div>
            <div class="mt-2 flex gap-2">
              <textarea v-model="d.metiersText" rows="3" placeholder="Un métier par ligne" :class="[inputCls, 'flex-1']" />
              <BaseButton size="sm" variant="ghost" @click="removeDept(i)">Retirer</BaseButton>
            </div>
          </div>
        </div>
        <p v-if="cartoError" class="mt-3 rounded-lg border border-warning/40 bg-warning-soft px-3 py-2 text-xs text-warning">
          {{ cartoError }}
        </p>
        <div class="mt-3 flex justify-end">
          <BaseButton :disabled="cartoBusy" @click="saveCarto">
            <AppIcon name="check" :size="15" /> {{ cartoBusy ? 'Enregistrement…' : 'Enregistrer la cartographie' }}
          </BaseButton>
        </div>
      </BaseCard>
    </div>
  </div>
</template>
