<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { TeamMember } from '@/types/manager'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseChip from '@/components/ui/BaseChip.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseAvatar from '@/components/ui/BaseAvatar.vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import BaseBreadcrumb from '@/components/ui/BaseBreadcrumb.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

const route = useRoute()
const { toast } = useToast()
const m = ref<TeamMember | null>(null)
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    m.value = (await apiService.getTeamMember(route.params.id as string)) ?? null
  } catch {
    error.value = 'Impossible de charger la fiche.'
  } finally {
    loading.value = false
  }
}
onMounted(load)
watch(() => route.params.id, load)

const showEval = ref(false)
const evalScore = ref('4')
const evalComment = ref('')
const evalBusy = ref(false)

async function submitEval() {
  const texte = evalComment.value.trim()
  evalBusy.value = true
  try {
    // L'appréciation nourrit l'extraction des compétences DÉMONTRÉES (source=éval).
    if (texte.length >= 10) {
      const n = await apiService.extraireEvaluation(route.params.id as string, texte, 'mission')
      toast(
        n > 0
          ? `Évaluation transmise · ${n} compétence(s) détectée(s) et ajoutée(s) au profil`
          : 'Évaluation transmise',
        'ok',
      )
      await load() // rafraîchit la fiche (compétences mises à jour)
    } else {
      toast('Évaluation transmise')
    }
    showEval.value = false
    evalComment.value = ''
  } catch {
    toast("Évaluation transmise (extraction des compétences indisponible)", 'info')
    showEval.value = false
  } finally {
    evalBusy.value = false
  }
}
</script>

<template>
  <LoadingState v-if="loading" label="Chargement de la fiche…" />
  <ErrorState v-else-if="error" :message="error">
    <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
  </ErrorState>
  <EmptyState v-else-if="!m" title="Collaborateur introuvable" text="Ce membre n'existe pas.">
    <template #action>
      <RouterLink :to="{ name: 'manager.equipe' }"><BaseButton size="sm">Retour à l'équipe</BaseButton></RouterLink>
    </template>
  </EmptyState>

  <div v-else>
    <BaseBreadcrumb :items="[{ label: 'Mon équipe', to: { name: 'manager.equipe' } }, { label: m.name }]" />

    <div class="grid gap-5 lg:grid-cols-[1fr_300px]">
      <div class="space-y-5">
        <BaseCard>
          <div class="flex flex-wrap items-center gap-4">
            <BaseAvatar :initials="m.initials" size="xl" />
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-center gap-2">
                <h2 class="font-display text-2xl font-bold text-ink">{{ m.name }}</h2>
                <BasePill v-if="m.flag === 'top'" tone="new">Haut potentiel</BasePill>
                <BasePill v-else-if="m.flag === 'watch'" tone="warn">À suivre</BasePill>
              </div>
              <p class="text-sm text-ink-3">{{ m.role }} · {{ m.seniority }} · éval {{ m.evalScore }}</p>
            </div>
            <div class="text-center">
              <div class="font-display text-2xl font-extrabold text-green-deep">{{ m.ring }}%</div>
              <div class="text-[10px] text-ink-3">profil</div>
            </div>
          </div>
        </BaseCard>

        <BaseCard title="Compétences">
          <div class="space-y-3">
            <div v-for="s in m.skills" :key="s.label">
              <div class="mb-1 flex justify-between text-xs">
                <span class="font-medium text-ink-2">{{ s.label }}</span>
                <span class="text-ink-3">{{ s.pct }}%</span>
              </div>
              <div class="h-1.5 overflow-hidden rounded-full bg-panel-2">
                <div class="h-full rounded-full bg-green" :style="{ width: s.pct + '%' }" />
              </div>
            </div>
          </div>
        </BaseCard>

        <div class="grid gap-5 sm:grid-cols-2">
          <BaseCard title="Points forts">
            <div class="flex flex-wrap gap-2"><BaseChip v-for="s in m.strengths" :key="s" tone="green">{{ s }}</BaseChip></div>
          </BaseCard>
          <BaseCard title="À développer">
            <div class="flex flex-wrap gap-2"><BaseChip v-for="g in m.gaps" :key="g" tone="gap">{{ g }}</BaseChip></div>
          </BaseCard>
        </div>

        <BaseCard title="Historique des évaluations">
          <div class="space-y-2">
            <div v-for="(e, i) in m.evals" :key="i" class="rounded-xl border border-border bg-panel p-3">
              <div class="flex items-center justify-between">
                <b class="text-sm text-ink">{{ e.period }} · {{ e.score }}</b>
                <span class="text-[11px] text-ink-3">{{ e.by }}</span>
              </div>
              <p class="mt-1 text-xs text-ink-2">{{ e.comment }}</p>
            </div>
          </div>
        </BaseCard>
      </div>

      <div class="space-y-5">
        <BaseCard title="Aspiration">
          <div class="rounded-xl border border-green-line bg-green-ghost p-3">
            <div class="flex items-center gap-2 text-green-deep">
              <AppIcon name="route" :size="15" /><b class="text-sm">{{ m.aspiration }}</b>
            </div>
            <p class="mt-1 text-xs text-ink-2">Horizon {{ m.aspirationHorizon }}</p>
          </div>
        </BaseCard>
        <BaseCard title="Actions">
          <div class="space-y-2">
            <BaseButton block @click="showEval = true">
              <AppIcon name="check" :size="15" /> Soumettre une évaluation
            </BaseButton>
            <RouterLink :to="{ name: 'manager.entretien' }" class="block">
              <BaseButton block variant="secondary"><AppIcon name="chat" :size="15" /> Préparer l'entretien</BaseButton>
            </RouterLink>
          </div>
        </BaseCard>
      </div>
    </div>

    <BaseModal v-model="showEval" :title="`Évaluer ${m.name}`">
      <div class="space-y-4">
        <div>
          <label class="mb-1.5 block text-xs font-semibold text-ink-2">Note globale</label>
          <div class="flex gap-1.5">
            <button
              v-for="n in 5"
              :key="n"
              type="button"
              class="grid h-9 w-9 place-items-center rounded-lg border text-sm font-bold transition"
              :class="Number(evalScore) >= n ? 'border-gold bg-gold-soft text-gold' : 'border-border text-ink-3'"
              @click="evalScore = String(n)"
            >
              ★
            </button>
          </div>
        </div>
        <div>
          <label class="mb-1.5 block text-xs font-semibold text-ink-2">Appréciation</label>
          <textarea
            v-model="evalComment"
            rows="3"
            placeholder="Bilan, points forts, axes de progrès…"
            class="w-full rounded-xl border border-border bg-paper px-3 py-2 text-sm outline-none focus:border-green-line"
          />
        </div>
      </div>
      <template #footer>
        <BaseButton variant="secondary" size="sm" :disabled="evalBusy" @click="showEval = false">Annuler</BaseButton>
        <BaseButton size="sm" :disabled="evalBusy" @click="submitEval">
          <AppIcon name="send" :size="14" /> {{ evalBusy ? 'Analyse…' : 'Transmettre' }}
        </BaseButton>
      </template>
    </BaseModal>
  </div>
</template>
