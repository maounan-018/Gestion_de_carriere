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

/* ---- Formulaire création / édition ---- */
type Kind = 'carriere' | 'mission'
const showForm = ref(false)
const editing = ref<Souhait | null>(null)
const saving = ref(false)
const form = ref<{ titre: string; kind: Kind; horizon: string; description: string }>({
  titre: '', kind: 'carriere', horizon: '', description: '',
})

function openNew() {
  editing.value = null
  form.value = { titre: '', kind: 'carriere', horizon: '', description: '' }
  showForm.value = true
}
function openEdit(s: Souhait) {
  editing.value = s
  form.value = {
    titre: s.title, kind: 'carriere',
    horizon: s.horizon === '—' ? '' : s.horizon, description: s.desc,
  }
  showForm.value = true
}

async function save() {
  const titre = form.value.titre.trim()
  if (!titre || saving.value) return
  saving.value = true
  const payload = {
    titre, kind: form.value.kind,
    horizon: form.value.horizon.trim() || undefined,
    description: form.value.description.trim() || undefined,
  }
  try {
    if (editing.value) {
      const s = editing.value
      const prev = { title: s.title, horizon: s.horizon, desc: s.desc }
      // Optimiste : le PATCH ne change ni le statut ni le « poussé ».
      s.title = titre
      s.horizon = payload.horizon || '—'
      s.desc = payload.description || ''
      try {
        await apiService.updateSouhait(s.id ?? '', payload)
        toast('Souhait mis à jour')
      } catch (e) {
        Object.assign(s, prev)
        throw e
      }
    } else {
      const created = await apiService.createSouhait(payload)
      items.value.unshift(created)
      toast('Souhait créé')
    }
    showForm.value = false
  } catch (e) {
    toast(e instanceof Error ? e.message : "Échec de l'enregistrement", 'error')
  } finally {
    saving.value = false
  }
}

const crumbs = [
  { label: 'Mon profil', to: { name: 'collab.profil' } },
  { label: "Souhaits d'évolution" },
]

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = (await apiService.getSouhaits()).map((s) => ({ ...s }))
  } catch {
    error.value = 'Impossible de charger vos souhaits.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

async function push(s: Souhait) {
  const prev = { pushed: s.pushed, status: s.status, tone: s.tone }
  s.pushed = true
  s.status = 'Poussé au manager'
  s.tone = 'new'
  try {
    await apiService.pushSouhait(s.id ?? '')
    toast('Souhait transmis à votre manager')
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
        <h3 class="text-sm font-bold text-green-deep">Vos souhaits guident vos recommandations</h3>
        <p class="text-xs text-ink-2">Les souhaits que vous poussez sont transmis à votre manager et alimentent le moteur de recommandations.</p>
      </div>
      <BaseButton @click="openNew()"><AppIcon name="route" :size="15" /> Nouveau souhait</BaseButton>
    </div>

    <LoadingState v-if="loading" label="Chargement de vos souhaits…" />
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
        <p v-if="!s.pushed" class="mt-2 text-xs text-ink-3">Ce souhait n'est visible que par vous tant que vous ne l'avez pas poussé à votre manager.</p>

        <div class="mt-3 flex flex-wrap gap-2">
          <BaseButton variant="secondary" size="sm" @click="openEdit(s)">Modifier</BaseButton>
          <BaseButton v-if="!s.pushed" size="sm" @click="push(s)"><AppIcon name="send" :size="14" /> Pousser au manager</BaseButton>
        </div>
      </BaseCard>
    </div>

    <BaseModal v-model="showForm" :title="editing ? 'Modifier le souhait' : 'Nouveau souhait'">
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
          <label class="block">
            <span class="mb-1 block text-xs font-semibold text-ink-2">Horizon</span>
            <input
              v-model="form.horizon"
              placeholder="Ex : 6-12 mois"
              class="w-full rounded-xl border border-border bg-panel px-3 py-2 text-sm outline-none focus:border-green"
            />
          </label>
        </div>
        <label class="block">
          <span class="mb-1 block text-xs font-semibold text-ink-2">Description</span>
          <textarea
            v-model="form.description"
            rows="3"
            placeholder="Précisez votre souhait, le contexte, ce qui vous motive…"
            class="w-full resize-none rounded-xl border border-border bg-panel px-3 py-2 text-sm outline-none focus:border-green"
          />
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
