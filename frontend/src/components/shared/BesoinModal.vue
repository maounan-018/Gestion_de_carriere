<script setup lang="ts">
/**
 * Exprimer un BESOIN de recrutement (manager) — transmis à la HRBP par le canal
 * officiel. Le manager choisit un poste (fiche de référence) et décrit le besoin ;
 * la HRBP validera puis publiera l'offre en continuité.
 */
import { ref, watch } from 'vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { FicheListItem } from '@/types/rh'
import BaseModal from '@/components/ui/BaseModal.vue'
import BaseButton from '@/components/ui/BaseButton.vue'

const props = defineProps<{ modelValue: boolean }>()
const emit = defineEmits<{ 'update:modelValue': [boolean]; created: [] }>()
const { toast } = useToast()

const inputCls =
  'w-full rounded-xl border border-border bg-panel px-3 py-2 text-sm text-ink outline-none focus:border-green-line'

const fiches = ref<FicheListItem[]>([])
const ficheId = ref<number | null>(null)
const poste = ref('')
const description = ref('')
const saving = ref(false)

watch(
  () => props.modelValue,
  async (open) => {
    if (!open) return
    ficheId.value = null
    poste.value = ''
    description.value = ''
    try {
      fiches.value = await apiService.getFiches()
    } catch {
      fiches.value = []
    }
  },
)

function onFicheChange() {
  const f = fiches.value.find((x) => x.id === ficheId.value)
  if (f) poste.value = f.intitule_poste
}

function close() {
  emit('update:modelValue', false)
}

async function submit() {
  if (saving.value || !poste.value.trim()) return
  saving.value = true
  try {
    await apiService.creerBesoin({
      ficheId: ficheId.value,
      poste: poste.value.trim(),
      description: description.value.trim(),
    })
    toast('Besoin transmis à la HRBP', 'ok')
    emit('created')
    close()
  } catch (e) {
    toast(e instanceof Error ? e.message : "Échec de l'envoi du besoin", 'error')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <BaseModal :model-value="modelValue" title="Exprimer un besoin de recrutement"
    @update:model-value="emit('update:modelValue', $event)">
    <div class="space-y-4">
      <p class="text-xs text-ink-3">
        Décrivez votre besoin sur un poste. Il sera transmis à la HRBP, qui le validera
        et publiera l'offre. Vous garderez la visibilité sur les candidatures.
      </p>
      <div>
        <label class="mb-1 block text-xs font-semibold text-ink-2">Poste concerné</label>
        <select v-model="ficheId" :class="inputCls" @change="onFicheChange">
          <option :value="null">Choisir un poste…</option>
          <option v-for="f in fiches" :key="f.id" :value="f.id">{{ f.intitule_poste }}</option>
        </select>
        <input
          v-model="poste"
          :class="inputCls"
          class="mt-2"
          maxlength="200"
          placeholder="Ou saisir un intitulé libre"
        />
      </div>
      <div>
        <label class="mb-1 block text-xs font-semibold text-ink-2">Description du besoin</label>
        <textarea
          v-model="description"
          rows="4"
          :class="inputCls"
          placeholder="Contexte, justification, profil recherché, échéance…"
        />
      </div>
    </div>
    <template #footer>
      <BaseButton variant="secondary" size="sm" @click="close">Annuler</BaseButton>
      <BaseButton size="sm" :disabled="saving || !poste.trim()" @click="submit">
        {{ saving ? 'Envoi…' : 'Transmettre à la HRBP' }}
      </BaseButton>
    </template>
  </BaseModal>
</template>
