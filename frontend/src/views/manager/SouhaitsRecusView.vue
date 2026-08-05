<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { SouhaitRecu, SouhaitRecuStatus } from '@/types/manager'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseAvatar from '@/components/ui/BaseAvatar.vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

const items = ref<SouhaitRecu[]>([])
const loading = ref(true)
const error = ref('')
const { toast } = useToast()

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = await apiService.getSouhaitsRecus()
  } catch {
    error.value = 'Impossible de charger les souhaits.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

function act(s: SouhaitRecu, status: SouhaitRecuStatus, msg: string) {
  s.status = status
  toast(msg)
}

// Transmettre un souhait « carrière » à la RH : une RECOMMANDATION justifiée est
// exigée (pourquoi le manager appuie ce collaborateur) et réellement envoyée à la RH.
const showTransmit = ref(false)
const curSouhait = ref<SouhaitRecu | null>(null)
const justification = ref('')
const transmitting = ref(false)

function openTransmit(s: SouhaitRecu) {
  curSouhait.value = s
  justification.value = ''
  showTransmit.value = true
}
async function confirmTransmit() {
  const s = curSouhait.value
  if (!s || !justification.value.trim() || transmitting.value) return
  transmitting.value = true
  try {
    await apiService.communiquerRH(
      `Recommandation · ${s.memberName} : ${s.title}`,
      `Souhait d'évolution « ${s.title} » (${s.horizon}). Pourquoi je recommande `
        + `${s.memberName} : ${justification.value.trim()}`,
    )
    s.status = 'transmis RH'
    showTransmit.value = false
    toast('Souhait transmis à la RH avec votre recommandation', 'ok')
  } catch (e) {
    toast(e instanceof Error ? e.message : 'Échec de la transmission', 'error')
  } finally {
    transmitting.value = false
  }
}

const statusTone: Record<string, 'new' | 'ai' | 'warn' | 'mut'> = {
  'à traiter': 'warn', accordé: 'new', 'transmis RH': 'ai', refusé: 'mut',
}
</script>

<template>
  <div class="space-y-4">
    <p class="text-sm text-ink-3">
      Souhaits d'évolution poussés par votre équipe. <b class="text-ink-2">Mission</b> : vous
      décidez · <b class="text-ink-2">Carrière</b> : vous transmettez à la RH.
    </p>

    <LoadingState v-if="loading" label="Chargement des souhaits…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>
    <EmptyState
      v-else-if="!items.length"
      title="Aucun souhait en attente"
      text="Aucun souhait d'évolution à traiter pour le moment."
    />

    <div v-else class="space-y-3">
      <BaseCard v-for="s in items" :key="s.id">
        <div class="flex flex-wrap items-start gap-3">
          <BaseAvatar :initials="s.memberInitials" size="md" />
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-2">
              <h4 class="text-sm font-bold text-ink">{{ s.title }}</h4>
              <BasePill :tone="s.kind === 'mission' ? 'ai' : 'new'">
                {{ s.kind === 'mission' ? 'Mission' : 'Carrière' }}
              </BasePill>
              <BasePill :tone="statusTone[s.status]">{{ s.status }}</BasePill>
            </div>
            <p class="text-xs text-ink-3">{{ s.memberName }} · {{ s.horizon }} · {{ s.date }}</p>
            <p class="mt-1 text-sm text-ink-2">{{ s.desc }}</p>
          </div>
        </div>
        <div v-if="s.status === 'à traiter'" class="mt-3 flex flex-wrap gap-2 border-t border-border pt-3">
          <template v-if="s.kind === 'mission'">
            <BaseButton size="sm" @click="act(s, 'accordé', 'Souhait accordé')">
              <AppIcon name="check" :size="14" /> Accorder
            </BaseButton>
            <BaseButton size="sm" variant="danger" @click="act(s, 'refusé', 'Souhait refusé · motif à préciser')">
              Refuser
            </BaseButton>
          </template>
          <BaseButton v-else size="sm" @click="openTransmit(s)">
            <AppIcon name="send" :size="14" /> Transmettre à la RH
          </BaseButton>
        </div>
      </BaseCard>
    </div>

    <BaseModal v-model="showTransmit" title="Transmettre à la RH">
      <div v-if="curSouhait" class="space-y-3">
        <div class="rounded-xl border border-green-line bg-green-ghost p-3">
          <h4 class="text-sm font-bold text-green-deep">{{ curSouhait.title }}</h4>
          <p class="text-xs text-ink-2">{{ curSouhait.memberName }} · {{ curSouhait.horizon }}</p>
        </div>
        <div>
          <label class="mb-1.5 block text-xs font-semibold text-ink-2">
            Pourquoi recommandez-vous {{ curSouhait.memberName }} ? <span class="text-danger">*</span>
          </label>
          <textarea
            v-model="justification"
            rows="4"
            placeholder="Points forts, réalisations, potentiel observé, adéquation avec l'évolution visée…"
            class="w-full rounded-xl border border-border bg-panel px-3 py-2 text-sm text-ink outline-none focus:border-green-line"
          />
          <p class="mt-1 text-[11px] text-ink-3">Votre recommandation est envoyée à la RH avec le souhait.</p>
        </div>
      </div>
      <template #footer>
        <BaseButton variant="secondary" size="sm" @click="showTransmit = false">Annuler</BaseButton>
        <BaseButton size="sm" :disabled="!justification.trim() || transmitting" @click="confirmTransmit">
          <AppIcon name="send" :size="14" /> {{ transmitting ? 'Transmission…' : 'Transmettre' }}
        </BaseButton>
      </template>
    </BaseModal>
  </div>
</template>
