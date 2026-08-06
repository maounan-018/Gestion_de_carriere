<script setup lang="ts">
/**
 * Éditer mon profil · composant PARTAGÉ (collaborateur / manager / RH).
 * Préremplit depuis /profils/me/carriere et sauvegarde via PATCH /profils/me
 * (champs auto-déclarés uniquement). Calqué sur la maquette : description, poste
 * visé, horizon, type d'évolution, zones géographiques, disponibilité, ambitions.
 */
import { ref, watch } from 'vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { MyCvStatus } from '@/types/domain'
import BaseModal from '@/components/ui/BaseModal.vue'
import BaseButton from '@/components/ui/BaseButton.vue'

const props = defineProps<{ modelValue: boolean }>()
const emit = defineEmits<{ 'update:modelValue': [boolean]; saved: [] }>()
const { toast } = useToast()

const PERIODES = ['semaines', 'mois', 'années'] as const
const TYPES = ['Management', 'Expertise', 'Mobilité géographique', 'Mission transverse']
const inputCls =
  'w-full rounded-xl border border-border bg-panel px-3 py-2 text-sm text-ink outline-none focus:border-green-line'

const loading = ref(false)
const saving = ref(false)
const posteActuel = ref('')
const posteVise = ref('')
const horizonNombre = ref<number | null>(null)
const horizonPeriode = ref<string>('mois')
const typeEvolution = ref('')
const mobiliteGeo = ref('')
const disponibilite = ref('')
const bio = ref('')
const aspirations = ref('')
const cv = ref<MyCvStatus | null>(null)
const cvUploading = ref(false)

/** Décompose un horizon texte ("6 mois", "1 an"…) en nombre + période. */
function parseHorizon(s: string): { nombre: number | null; periode: string } {
  const m = (s || '').match(/(\d+)/)
  const low = (s || '').toLowerCase()
  const periode = low.includes('semaine') ? 'semaines'
    : (low.includes('an') || low.includes('année')) ? 'années' : 'mois'
  return { nombre: m ? parseInt(m[1], 10) : null, periode }
}

watch(
  () => props.modelValue,
  async (open) => {
    if (!open) return
    loading.value = true
    try {
      const p = await apiService.getMyProfilEditable()
      posteActuel.value = p?.poste_actuel ?? ''
      posteVise.value = p?.poste_vise ?? ''
      const h = parseHorizon(p?.horizon ?? '')
      horizonNombre.value = h.nombre
      horizonPeriode.value = h.periode
      typeEvolution.value = p?.type_evolution ?? ''
      mobiliteGeo.value = p?.mobilite_geo ?? ''
      disponibilite.value = p?.disponibilite ?? ''
      bio.value = p?.bio ?? ''
      aspirations.value = p?.aspirations ?? ''
      cv.value = await apiService.getMyCvStatus()
    } finally {
      loading.value = false
    }
  },
)

function close() {
  emit('update:modelValue', false)
}

async function save() {
  if (saving.value) return
  saving.value = true
  try {
    await apiService.updateMyProfil({
      poste_actuel: posteActuel.value.trim(),
      poste_vise: posteVise.value.trim(),
      horizon: horizonNombre.value ? `${horizonNombre.value} ${horizonPeriode.value}` : '',
      type_evolution: typeEvolution.value,
      mobilite_geo: mobiliteGeo.value.trim(),
      disponibilite: disponibilite.value.trim(),
      bio: bio.value.trim(),
      aspirations: aspirations.value.trim(),
    })
    toast('Profil mis à jour', 'ok')
    emit('saved')
    close()
  } catch (e) {
    toast(e instanceof Error ? e.message : 'Échec de la mise à jour', 'error')
  } finally {
    saving.value = false
  }
}

/** Met à jour le CV : le nouveau fichier est vu par tous ceux qui peuvent le consulter. */
async function remplacerCv(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  cvUploading.value = true
  try {
    cv.value = await apiService.uploaderMonCv(file)
    toast('CV mis à jour', 'ok')
  } catch (err) {
    toast(err instanceof Error ? err.message : 'Échec de la mise à jour du CV', 'error')
  } finally {
    cvUploading.value = false
    ;(e.target as HTMLInputElement).value = ''
  }
}
</script>

<template>
  <BaseModal
    :model-value="modelValue"
    title="Éditer mon profil"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div v-if="loading" class="py-8 text-center text-sm text-ink-3">Chargement de votre profil…</div>
    <div v-else class="space-y-4">
      <!-- Informations générales -->
      <div>
        <label class="mb-1 block text-xs font-semibold text-ink-2">Poste actuel</label>
        <input v-model="posteActuel" :class="inputCls" maxlength="200" placeholder="Ex : Analyste Risque Senior" />
      </div>
      <div>
        <label class="mb-1 block text-xs font-semibold text-ink-2">Description / à propos</label>
        <textarea
          v-model="bio"
          rows="3"
          :class="inputCls"
          placeholder="Décrivez votre parcours en quelques lignes…"
        />
      </div>

      <!-- CV : visualiser / télécharger / mettre à jour (répercuté pour tous les viewers) -->
      <div>
        <label class="mb-1 block text-xs font-semibold text-ink-2">Mon CV (PDF)</label>
        <div
          v-if="cv?.filename"
          class="flex items-center justify-between gap-3 rounded-xl border border-border bg-panel px-3 py-2"
        >
          <a
            :href="apiService.cvUrl(cv.profilId)"
            target="_blank"
            rel="noopener"
            class="min-w-0 truncate text-sm font-semibold text-green-deep hover:underline"
          >
            {{ cv.filename }}
          </a>
          <span class="shrink-0 text-[11px] text-ink-3">Ouvrir / télécharger</span>
        </div>
        <p v-else class="text-sm text-ink-3">Aucun CV pour l'instant.</p>
        <label
          class="mt-2 inline-flex cursor-pointer items-center gap-2 text-xs font-semibold text-green-deep hover:underline"
        >
          {{ cvUploading ? 'Envoi…' : cv?.filename ? 'Remplacer le CV' : 'Ajouter un CV' }}
          <input
            type="file"
            accept="application/pdf,.pdf"
            class="hidden"
            :disabled="cvUploading"
            @change="remplacerCv"
          />
        </label>
        <p class="mt-1 text-[11px] text-ink-3">
          Visible par votre manager et la HRBP. Toute mise à jour est répercutée pour tous ceux qui le consultent.
        </p>
      </div>

      <div class="h-px bg-border" />
      <p class="text-xs font-semibold uppercase tracking-wide text-green-deep">Aspirations &amp; poste visé</p>

      <div>
        <label class="mb-1 block text-xs font-semibold text-ink-2">Poste visé</label>
        <input v-model="posteVise" :class="inputCls" maxlength="200" placeholder="Ex : Manager d'équipe Risques" />
      </div>
      <div>
        <label class="mb-1 block text-xs font-semibold text-ink-2">Horizon</label>
        <div class="flex gap-2">
          <input
            v-model.number="horizonNombre"
            type="number"
            min="1"
            :class="inputCls"
            class="max-w-[7rem]"
            placeholder="Ex : 3"
          />
          <select v-model="horizonPeriode" :class="inputCls" class="max-w-[11rem]">
            <option v-for="pr in PERIODES" :key="pr" :value="pr">{{ pr }}</option>
          </select>
        </div>
      </div>
      <div>
        <label class="mb-1 block text-xs font-semibold text-ink-2">Type d'évolution souhaitée</label>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="t in TYPES"
            :key="t"
            type="button"
            class="rounded-full border px-3 py-1.5 text-xs font-semibold transition"
            :class="typeEvolution === t ? 'border-green-line bg-green-soft text-green-deep' : 'border-border text-ink-3 hover:border-green-line'"
            @click="typeEvolution = typeEvolution === t ? '' : t"
          >
            {{ t }}
          </button>
        </div>
      </div>
      <div class="grid gap-3 sm:grid-cols-2">
        <div>
          <label class="mb-1 block text-xs font-semibold text-ink-2">Zones géographiques</label>
          <input v-model="mobiliteGeo" :class="inputCls" maxlength="200" placeholder="Casablanca · Paris…" />
        </div>
        <div>
          <label class="mb-1 block text-xs font-semibold text-ink-2">Disponibilité</label>
          <input v-model="disponibilite" :class="inputCls" maxlength="64" placeholder="Ex : 6 à 12 mois" />
        </div>
      </div>
      <div>
        <label class="mb-1 block text-xs font-semibold text-ink-2">Mes ambitions (texte libre)</label>
        <textarea
          v-model="aspirations"
          rows="3"
          :class="inputCls"
          placeholder="Décrivez ce que vous visez et pourquoi…"
        />
        <p class="mt-1 text-[11px] text-ink-3">
          Vos aspirations orientent vos recommandations et aident manager et RH à préparer vos entretiens.
        </p>
      </div>

      <div class="flex justify-end gap-2 pt-1">
        <BaseButton variant="secondary" size="sm" @click="close">Annuler</BaseButton>
        <BaseButton size="sm" :disabled="saving" @click="save">
          {{ saving ? 'Enregistrement…' : 'Enregistrer' }}
        </BaseButton>
      </div>
    </div>
  </BaseModal>
</template>
