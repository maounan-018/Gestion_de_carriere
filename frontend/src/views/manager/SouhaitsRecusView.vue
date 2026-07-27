<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { SouhaitRecu, SouhaitRecuStatus } from '@/types/manager'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseAvatar from '@/components/ui/BaseAvatar.vue'
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
          <BaseButton v-else size="sm" @click="act(s, 'transmis RH', 'Souhait transmis à la RH')">
            <AppIcon name="send" :size="14" /> Transmettre à la RH
          </BaseButton>
        </div>
      </BaseCard>
    </div>
  </div>
</template>
