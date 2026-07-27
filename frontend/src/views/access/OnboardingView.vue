<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ShieldCheck, User } from 'lucide-vue-next'
import AuthCard from '@/components/access/AuthCard.vue'
import AuthStepper from '@/components/access/AuthStepper.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import LoadingState from '@/components/ui/LoadingState.vue'

const router = useRouter()

const entities = [
  'Banque de Détail',
  'Corporate & Investment',
  'Risques',
  'IT & Digital',
  'Finance',
  'Ressources Humaines',
  'Audit & Conformité',
]
const postes = ['Analyste', "Chargé d'Affaires", 'Chef de projet', 'Manager', 'Directeur de Pôle']

const displayName = ref('Marc')
const entity = ref('')
const poste = ref('')
const verifying = ref(false)
const canFinish = computed(() => !!(displayName.value.trim() && entity.value && poste.value))

function finish() {
  verifying.value = true
  window.setTimeout(() => {
    verifying.value = false
    router.push({ name: 'bienvenue' })
  }, 1200)
}
</script>

<template>
  <AuthCard>
    <AuthStepper :active="2" />
    <h1 class="font-display text-xl font-bold text-ink">Configurons votre profil</h1>
    <p class="mt-1 text-sm text-ink-3">
      Vérifié en temps réel dans l'annuaire BMCI · modifiable plus tard.
    </p>

    <div v-if="!verifying" class="mt-5 space-y-4">
      <div>
        <label for="onb-name" class="mb-1 block text-xs font-semibold text-ink-2">
          Comment souhaitez-vous être appelé ?
        </label>
        <div
          class="flex items-center gap-2 rounded-xl border border-border bg-paper px-3 focus-within:border-green-line"
        >
          <User :size="16" class="text-ink-3" />
          <input
            id="onb-name"
            v-model="displayName"
            placeholder="Ex : Marc"
            class="w-full bg-transparent py-2.5 text-sm text-ink outline-none"
          />
        </div>
        <p class="mt-1 text-[11px] text-ink-3">
          Visible par vous et votre Coach. Les autres vous identifient par votre e-mail pro.
        </p>
      </div>

      <div>
        <label for="onb-entity" class="mb-1 block text-xs font-semibold text-ink-2">Votre entité</label>
        <select
          id="onb-entity"
          v-model="entity"
          class="w-full rounded-xl border border-border bg-paper px-3 py-2.5 text-sm text-ink outline-none focus:border-green-line"
        >
          <option value="" disabled>Sélectionnez…</option>
          <option v-for="e in entities" :key="e" :value="e">{{ e }}</option>
        </select>
      </div>

      <div>
        <label for="onb-poste" class="mb-1 block text-xs font-semibold text-ink-2">Votre poste actuel</label>
        <select
          id="onb-poste"
          v-model="poste"
          class="w-full rounded-xl border border-border bg-paper px-3 py-2.5 text-sm text-ink outline-none focus:border-green-line"
        >
          <option value="" disabled>Sélectionnez…</option>
          <option v-for="p in postes" :key="p" :value="p">{{ p }}</option>
        </select>
      </div>

      <BaseButton block :disabled="!canFinish" @click="finish">
        <ShieldCheck :size="16" /> Vérifier &amp; terminer
      </BaseButton>
      <p class="text-center text-xs text-ink-3">
        <button class="hover:text-green-deep" @click="router.push({ name: 'onboardingErreur' })">
          Voir le cas où l'annuaire ne concorde pas
        </button>
      </p>
    </div>

    <LoadingState v-else label="Vérification dans l'annuaire BMCI…" />
  </AuthCard>
</template>
