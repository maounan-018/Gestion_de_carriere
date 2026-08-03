<script setup lang="ts">
/**
 * Éditer mon profil — composant PARTAGÉ (collaborateur / manager / RH).
 * Préremplit depuis /profils/me/carriere et sauvegarde via PATCH /profils/me
 * (champs auto-déclarés uniquement). Calqué sur la maquette : description, poste
 * visé, horizon, type d'évolution, zones géographiques, disponibilité, ambitions.
 */
import { ref, watch } from 'vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import BaseModal from '@/components/ui/BaseModal.vue'
import BaseButton from '@/components/ui/BaseButton.vue'

const props = defineProps<{ modelValue: boolean }>()
const emit = defineEmits<{ 'update:modelValue': [boolean]; saved: [] }>()
const { toast } = useToast()

const HORIZONS = ['6 mois', '1 an', '2-3 ans']
const TYPES = ['Management', 'Expertise', 'Mobilité géographique', 'Mission transverse']
const inputCls =
  'w-full rounded-xl border border-border bg-panel px-3 py-2 text-sm text-ink outline-none focus:border-green-line'

const loading = ref(false)
const saving = ref(false)
const posteActuel = ref('')
const posteVise = ref('')
const horizon = ref('')
const typeEvolution = ref('')
const mobiliteGeo = ref('')
const disponibilite = ref('')
const bio = ref('')
const aspirations = ref('')

watch(
  () => props.modelValue,
  async (open) => {
    if (!open) return
    loading.value = true
    try {
      const p = await apiService.getMyProfilEditable()
      posteActuel.value = p?.poste_actuel ?? ''
      posteVise.value = p?.poste_vise ?? ''
      horizon.value = p?.horizon ?? ''
      typeEvolution.value = p?.type_evolution ?? ''
      mobiliteGeo.value = p?.mobilite_geo ?? ''
      disponibilite.value = p?.disponibilite ?? ''
      bio.value = p?.bio ?? ''
      aspirations.value = p?.aspirations ?? ''
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
      horizon: horizon.value,
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

      <div class="h-px bg-border" />
      <p class="text-xs font-semibold uppercase tracking-wide text-green-deep">Aspirations &amp; poste visé</p>

      <div>
        <label class="mb-1 block text-xs font-semibold text-ink-2">Poste visé</label>
        <input v-model="posteVise" :class="inputCls" maxlength="200" placeholder="Ex : Manager d'équipe Risques" />
      </div>
      <div>
        <label class="mb-1 block text-xs font-semibold text-ink-2">Horizon</label>
        <div class="flex gap-2">
          <button
            v-for="h in HORIZONS"
            :key="h"
            type="button"
            class="rounded-lg border px-3 py-1.5 text-xs font-semibold transition"
            :class="horizon === h ? 'border-green-line bg-green-soft text-green-deep' : 'border-border text-ink-3 hover:border-green-line'"
            @click="horizon = horizon === h ? '' : h"
          >
            {{ h }}
          </button>
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
