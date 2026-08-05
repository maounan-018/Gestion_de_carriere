<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { Souhait } from '@/types/domain'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseBreadcrumb from '@/components/ui/BaseBreadcrumb.vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const items = ref<Souhait[]>([])
const loading = ref(true)
const error = ref('')
const { toast } = useToast()

/* ---- Horizon = nombre + période (jours / semaines / mois / ans) ---- */
const PERIODS = [
  { value: 'jours', one: 'jour', many: 'jours' },
  { value: 'semaines', one: 'semaine', many: 'semaines' },
  { value: 'mois', one: 'mois', many: 'mois' },
  { value: 'ans', one: 'an', many: 'ans' },
] as const
type PeriodVal = (typeof PERIODS)[number]['value']
function composeHorizon(num: string, period: PeriodVal): string {
  const n = parseInt(num, 10)
  if (!n || n < 1) return ''
  const p = PERIODS.find((x) => x.value === period) ?? PERIODS[2]
  return `${n} ${n === 1 ? p.one : p.many}`
}
function parseHorizon(h: string): { num: string; period: PeriodVal } {
  const m = h.match(/(\d+)\s*(jour|semaine|mois|an)/i)
  if (!m) return { num: '', period: 'mois' }
  const u = m[2].toLowerCase()
  const period: PeriodVal = u.startsWith('jour') ? 'jours' : u.startsWith('semaine')
    ? 'semaines' : u.startsWith('an') ? 'ans' : 'mois'
  return { num: m[1], period }
}

/* ---- Formulaire création / édition ---- */
type Kind = 'carriere' | 'mission'
const showForm = ref(false)
const editing = ref<Souhait | null>(null)
const saving = ref(false)
const form = ref<{ titre: string; kind: Kind; horizonNum: string; horizonPeriod: PeriodVal; description: string; pushNow: boolean }>({
  titre: '', kind: 'carriere', horizonNum: '', horizonPeriod: 'mois', description: '', pushNow: false,
})

function openNew() {
  editing.value = null
  form.value = { titre: '', kind: 'carriere', horizonNum: '', horizonPeriod: 'mois', description: '', pushNow: false }
  showForm.value = true
}
function openEdit(s: Souhait) {
  editing.value = s
  const { num, period } = parseHorizon(s.horizon === '—' ? '' : s.horizon)
  form.value = { titre: s.title, kind: 'carriere', horizonNum: num, horizonPeriod: period, description: s.desc, pushNow: false }
  showForm.value = true
}

async function save() {
  const titre = form.value.titre.trim()
  if (!titre || saving.value) return
  saving.value = true
  const payload = {
    titre, kind: form.value.kind,
    horizon: composeHorizon(form.value.horizonNum, form.value.horizonPeriod) || undefined,
    description: form.value.description.trim() || undefined,
  }
  try {
    if (editing.value) {
      await apiService.updateSouhait(editing.value.id ?? '', payload)
      toast('Demande mise à jour')
    } else {
      await apiService.createSouhait({ ...payload, pushed: form.value.pushNow })
      toast(form.value.pushNow ? "Demande créée et transmise à votre manager" : 'Demande créée')
    }
    showForm.value = false
    await load() // refetch → cohérence sur tous les écrans qui l'affichent
  } catch (e) {
    toast(e instanceof Error ? e.message : "Échec de l'enregistrement", 'error')
  } finally {
    saving.value = false
  }
}

const crumbs = [
  { label: 'Mon profil', to: { name: 'collab.profil' } },
  { label: "Mes demandes d'évolution" },
]

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = (await apiService.getSouhaits()).map((s) => ({ ...s }))
  } catch {
    error.value = 'Impossible de charger vos demandes.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

async function push(s: Souhait) {
  const prev = { pushed: s.pushed, status: s.status, tone: s.tone }
  s.pushed = true
  s.status = 'Transmise au manager'
  s.tone = 'new'
  try {
    await apiService.pushSouhait(s.id ?? '')
    toast('Demande transmise à votre manager')
    await load() // cohérence avec les écrans qui affichent les demandes reçues
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
        <h3 class="text-sm font-bold text-green-deep">Vos demandes d'évolution guident vos recommandations</h3>
        <p class="text-xs text-ink-2">Les demandes que vous transmettez sont envoyées à votre manager et alimentent le moteur de recommandations.</p>
      </div>
      <BaseButton @click="openNew()"><AppIcon name="route" :size="15" /> Nouvelle demande</BaseButton>
    </div>

    <LoadingState v-if="loading" label="Chargement de vos demandes…" />
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
        <p v-if="!s.pushed" class="mt-2 text-xs text-ink-3">Cette demande n'est visible que par vous tant que vous ne l'avez pas transmise à votre manager.</p>

        <div class="mt-3 flex flex-wrap gap-2">
          <BaseButton variant="secondary" size="sm" @click="openEdit(s)">Modifier</BaseButton>
          <BaseButton v-if="!s.pushed" size="sm" @click="push(s)"><AppIcon name="send" :size="14" /> Transmettre au manager</BaseButton>
        </div>
      </BaseCard>
    </div>

    <BaseModal v-model="showForm" :title="editing ? 'Modifier la demande' : 'Nouvelle demande'">
      <form class="space-y-4" @submit.prevent="save">
        <label class="block">
          <span class="mb-1 block text-xs font-semibold text-ink-2">Intitulé</span>
          <input
            v-model="form.titre"
            placeholder="Ex : Manager d'équipe Risques"
            class="w-full rounded-xl border border-border bg-panel px-3 py-2 text-sm outline-none focus:border-green"
          />
        </label>
        <div class="grid gap-4 sm:grid-cols-2">
          <label class="block">
            <span class="mb-1 block text-xs font-semibold text-ink-2">Type</span>
            <select
              v-model="form.kind"
              class="w-full rounded-xl border border-border bg-panel px-3 py-2 text-sm outline-none focus:border-green"
            >
              <option value="carriere">Évolution de carrière</option>
              <option value="mission">Mission / projet</option>
            </select>
          </label>
          <div class="block">
            <span class="mb-1 block text-xs font-semibold text-ink-2">Horizon</span>
            <div class="flex gap-2">
              <input
                v-model="form.horizonNum"
                type="number"
                min="1"
                placeholder="Ex : 6"
                class="w-20 rounded-xl border border-border bg-panel px-3 py-2 text-sm outline-none focus:border-green"
              />
              <select
                v-model="form.horizonPeriod"
                class="flex-1 rounded-xl border border-border bg-panel px-3 py-2 text-sm outline-none focus:border-green"
              >
                <option v-for="p in PERIODS" :key="p.value" :value="p.value">{{ p.many }}</option>
              </select>
            </div>
          </div>
        </div>
        <label class="block">
          <span class="mb-1 block text-xs font-semibold text-ink-2">Description</span>
          <textarea
            v-model="form.description"
            rows="3"
            placeholder="Précisez votre demande, le contexte, ce qui vous motive…"
            class="w-full resize-none rounded-xl border border-border bg-panel px-3 py-2 text-sm outline-none focus:border-green"
          />
        </label>
        <label v-if="!editing" class="flex items-start gap-2.5 rounded-xl border border-green-line bg-green-soft p-3">
          <input v-model="form.pushNow" type="checkbox" class="mt-0.5 h-4 w-4 accent-green" />
          <span class="text-xs text-ink-2">
            <b class="text-green-deep">Transmettre à mon manager maintenant.</b>
            Sinon, la demande reste <b>privée</b> · visible de vous seul · jusqu'à ce que vous décidiez de la transmettre.
          </span>
        </label>
      </form>
      <template #footer>
        <BaseButton variant="secondary" size="sm" @click="showForm = false">Annuler</BaseButton>
        <BaseButton size="sm" :disabled="saving || !form.titre.trim()" @click="save">
          <AppIcon name="send" :size="14" /> {{ editing ? 'Enregistrer' : 'Créer' }}
        </BaseButton>
      </template>
    </BaseModal>
  </div>
</template>
