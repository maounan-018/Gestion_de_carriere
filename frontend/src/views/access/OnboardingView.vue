<script setup lang="ts">
/**
 * Enrôlement (étape 3) — ACTIVATION d'un compte pré-existant. Les collaborateurs
 * BMCI existent déjà en base : poste, département et manager sont RÉCUPÉRÉS depuis
 * l'annuaire (pré-remplis, en lecture seule), jamais ressaisis. Le collaborateur
 * complètera ensuite ses aspirations dans « Éditer mon profil » ; ses compétences
 * seront évaluées par son manager. But démo : montrer que la donnée est réelle et
 * circule (les recommandations ne sont pas en dur).
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ShieldCheck, User, Briefcase, Building2, Users as UsersIcon } from '@lucide/vue'
import { apiService } from '@/services/apiService'
import AuthCard from '@/components/access/AuthCard.vue'
import AuthStepper from '@/components/access/AuthStepper.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import LoadingState from '@/components/ui/LoadingState.vue'

const router = useRouter()

type Preload = {
  found: boolean; nom?: string; prenom?: string
  poste_actuel?: string; departement?: string; manager_nom?: string
}
const loading = ref(true)
const verifying = ref(false)
const info = ref<Preload | null>(null)
const displayName = ref('')

onMounted(async () => {
  const email = sessionStorage.getItem('bmci-enroll-email') || ''
  try {
    const r = await apiService.annuairePreload(email)
    if (!r.found) {
      router.replace({ name: 'onboardingErreur' }) // e-mail hors annuaire → cas incohérence
      return
    }
    info.value = r
    displayName.value = r.prenom || ''
  } catch {
    router.replace({ name: 'onboardingErreur' })
    return
  } finally {
    loading.value = false
  }
})

const canFinish = computed(() => !!displayName.value.trim())

function finish() {
  verifying.value = true
  window.setTimeout(() => {
    verifying.value = false
    sessionStorage.removeItem('bmci-enroll-email')
    router.push({ name: 'bienvenue' })
  }, 900)
}
</script>

<template>
  <AuthCard>
    <AuthStepper :active="2" />
    <h1 class="font-display text-xl font-bold text-ink">Vos informations sont déjà là</h1>
    <p class="mt-1 text-sm text-ink-3">
      Récupérées depuis l'annuaire BMCI · vous n'avez rien à ressaisir.
    </p>

    <LoadingState v-if="loading" label="Récupération de votre fiche dans l'annuaire BMCI…" />
    <LoadingState v-else-if="verifying" label="Activation de votre compte…" />

    <div v-else-if="info" class="mt-5 space-y-4">
      <!-- Champs PRÉ-REMPLIS depuis la base (lecture seule) -->
      <div class="space-y-2.5 rounded-xl border border-green-line bg-green-ghost p-3.5">
        <div class="flex items-center gap-2.5 text-sm">
          <Briefcase :size="15" class="shrink-0 text-green-deep" />
          <span class="text-ink-3">Poste actuel</span>
          <b class="ml-auto text-right text-ink">{{ info.poste_actuel || '—' }}</b>
        </div>
        <div class="flex items-center gap-2.5 text-sm">
          <Building2 :size="15" class="shrink-0 text-green-deep" />
          <span class="text-ink-3">Département</span>
          <b class="ml-auto text-right text-ink">{{ info.departement || '—' }}</b>
        </div>
        <div class="flex items-center gap-2.5 text-sm">
          <UsersIcon :size="15" class="shrink-0 text-green-deep" />
          <span class="text-ink-3">Manager</span>
          <b class="ml-auto text-right text-ink">{{ info.manager_nom || '—' }}</b>
        </div>
      </div>

      <div>
        <label for="onb-name" class="mb-1 block text-xs font-semibold text-ink-2">
          Comment souhaitez-vous être appelé ?
        </label>
        <div class="flex items-center gap-2 rounded-xl border border-border bg-paper px-3 focus-within:border-green-line">
          <User :size="16" class="text-ink-3" />
          <input
            id="onb-name"
            v-model="displayName"
            placeholder="Ex : Youssef"
            class="w-full bg-transparent py-2.5 text-sm text-ink outline-none"
          />
        </div>
      </div>

      <div class="rounded-xl border border-border bg-panel px-3 py-2.5 text-[12px] leading-relaxed text-ink-2">
        Prochaine étape : renseignez vos <b>aspirations</b> dans « Éditer mon profil ». Vos
        <b>compétences</b> seront évaluées par votre manager — elles alimenteront vos
        recommandations et les opportunités internes proposées.
      </div>

      <BaseButton block :disabled="!canFinish" @click="finish">
        <ShieldCheck :size="16" /> Activer mon compte
      </BaseButton>
    </div>
  </AuthCard>
</template>
