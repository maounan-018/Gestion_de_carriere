<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { BookOpen } from '@lucide/vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { GabaritDoc, GabaritKind, CartoDoc } from '@/types/referentiel'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseBreadcrumb from '@/components/ui/BaseBreadcrumb.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const { toast } = useToast()

const KINDS: GabaritKind[] = ['metadata', 'freetext', 'skill_list', 'languages', 'kpi']
const CATEGORIES = ['metier', 'comportementale', 'transversale', 'outil_technologie']
const needsCategorie = (k: GabaritKind) => k === 'freetext' || k === 'skill_list'
const inputCls =
  'w-full rounded-lg border border-border bg-paper px-2.5 py-1.5 text-sm outline-none focus:border-green-line'

// Référentiels ouverts mobilisés (attribution légale — statique, informatif).
const referentiels = [
  { code: 'ESCO', name: 'Skills, Competences & Occupations', role: 'Compétences & métiers', licence: 'CC BY 4.0' },
  { code: 'O*NET', name: 'Occupational Information Network', role: 'Aptitudes & activités', licence: 'CC BY 4.0' },
  { code: 'SFIA', name: 'Skills Framework for the Information Age', role: 'Niveaux 1→7', licence: 'Licence SFIA' },
]

// ---- État -----------------------------------------------------------------
const loading = ref(true)
const loadError = ref('')

const gabarit = ref<GabaritDoc>({ version: null, sections: [] })
const gabError = ref('')
const gabBusy = ref(false)

interface DeptEdit { key: string; nom: string; pole: string; metiersText: string }
const depts = ref<DeptEdit[]>([])
const cartoVersion = ref<number | null>(null)
const cartoError = ref('')
const cartoBusy = ref(false)

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const [g, c] = await Promise.all([apiService.getGabarit(), apiService.getCartographie()])
    gabarit.value = g
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

// ---- Gabarit --------------------------------------------------------------
function addSection() {
  gabarit.value.sections.push({ key: '', label: '', kind: 'metadata', categorie: null, aide: '' })
}
function removeSection(i: number) {
  gabarit.value.sections.splice(i, 1)
}
async function saveGabarit() {
  gabError.value = ''
  gabBusy.value = true
  try {
    const doc: GabaritDoc = {
      version: gabarit.value.version ?? null,
      sections: gabarit.value.sections.map((s) => ({
        key: s.key.trim(),
        label: s.label.trim(),
        kind: s.kind,
        categorie: needsCategorie(s.kind) ? (s.categorie || null) : null,
        aide: (s.aide ?? '').trim() || null,
      })),
    }
    gabarit.value = await apiService.saveGabarit(doc)
    toast('Gabarit enregistré', 'ok')
  } catch (e) {
    gabError.value = (e as Error)?.message || 'Enregistrement refusé.'
  } finally {
    gabBusy.value = false
  }
}

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
</script>

<template>
  <div>
    <BaseBreadcrumb
      :items="[{ label: 'Supervision', to: { name: 'rh.supervision' } }, { label: 'Référentiel & gabarit' }]"
    />

    <BaseCard class="mb-4">
      <div class="flex items-center gap-3">
        <div class="grid h-10 w-10 place-items-center rounded-xl bg-green-soft text-green-deep">
          <BookOpen :size="18" />
        </div>
        <div class="min-w-0">
          <h1 class="font-display text-lg font-bold text-ink">Référentiel & gabarit — édition</h1>
          <p class="text-sm text-ink-3">
            Le socle qui structure les fiches de poste, la cartographie et le matching. Édition réservée RH/Admin ;
            chaque enregistrement est validé côté serveur (un référentiel invalide est refusé).
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
      <!-- Gabarit -->
      <BaseCard title="Gabarit de fiche de poste">
        <template #actions>
          <BaseButton size="sm" variant="ghost" @click="addSection">+ Ajouter une section</BaseButton>
        </template>
        <p class="mb-3 text-xs text-ink-3">
          Structure imposée à toute fiche. <b>kind</b> pilote le traitement ; <b>catégorie</b> requise pour
          freetext / skill_list.
        </p>
        <div class="space-y-2">
          <div v-for="(s, i) in gabarit.sections" :key="i" class="rounded-xl border border-border bg-panel p-2.5">
            <div class="grid gap-2 sm:grid-cols-[130px_1fr_140px]">
              <input v-model="s.key" placeholder="clé" :class="inputCls" />
              <input v-model="s.label" placeholder="Libellé" :class="inputCls" />
              <select v-model="s.kind" :class="inputCls">
                <option v-for="k in KINDS" :key="k" :value="k">{{ k }}</option>
              </select>
            </div>
            <div class="mt-2 grid items-center gap-2 sm:grid-cols-[150px_1fr_auto]">
              <select v-if="needsCategorie(s.kind)" v-model="s.categorie" :class="inputCls">
                <option :value="null" disabled>catégorie…</option>
                <option v-for="c in CATEGORIES" :key="c" :value="c">{{ c }}</option>
              </select>
              <span v-else class="text-xs text-ink-3">— (pas de catégorie)</span>
              <input v-model="s.aide" placeholder="Aide (optionnel)" :class="inputCls" />
              <BaseButton size="sm" variant="ghost" @click="removeSection(i)">Retirer</BaseButton>
            </div>
          </div>
        </div>
        <p v-if="gabError" class="mt-3 rounded-lg border border-warning/40 bg-warning-soft px-3 py-2 text-xs text-warning">
          {{ gabError }}
        </p>
        <div class="mt-3 flex justify-end">
          <BaseButton :disabled="gabBusy" @click="saveGabarit">
            <AppIcon name="check" :size="15" /> {{ gabBusy ? 'Enregistrement…' : 'Enregistrer le gabarit' }}
          </BaseButton>
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
