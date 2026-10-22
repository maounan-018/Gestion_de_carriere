<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { User, Mail, Lock, Eye, EyeOff, Check } from '@lucide/vue'
import { useToast } from '@/composables/useToast'
import AuthCard from '@/components/access/AuthCard.vue'
import AuthStepper from '@/components/access/AuthStepper.vue'
import BaseButton from '@/components/ui/BaseButton.vue'

const router = useRouter()
const { toast } = useToast()

const name = ref('')
const email = ref('')
const password = ref('')
const showPwd = ref(false)

const emailValid = computed(() => /^[^@\s.]+\.[^@\s]+@bmci.local$/i.test(email.value.trim()))
const criteria = computed(() => ({
  len: password.value.length >= 8,
  upper: /[A-Z]/.test(password.value),
  lower: /[a-z]/.test(password.value),
  digit: /\d/.test(password.value),
  special: /[^A-Za-z0-9]/.test(password.value),
}))
const strength = computed(() => Object.values(criteria.value).filter(Boolean).length)
const pwdValid = computed(() => strength.value === 5)
const canSubmit = computed(
  () => name.value.trim().length > 1 && emailValid.value && pwdValid.value,
)

const critList = [
  ['len', '8 caractères min.'],
  ['upper', 'Une majuscule'],
  ['lower', 'Une minuscule'],
  ['digit', 'Un chiffre'],
  ['special', 'Un caractère spécial'],
] as const

const strengthColor = computed(
  () => ['bg-danger', 'bg-danger', 'bg-warning', 'bg-warning', 'bg-green'][strength.value - 1] || '',
)
const strengthLabel = computed(
  () => ['Très faible', 'Faible', 'Moyen', 'Bon', 'Excellent'][strength.value - 1] || '',
)

function submit() {
  if (!canSubmit.value) return
  // Enrôlement : on transporte l'e-mail vers l'étape de vérification puis de
  // pré-remplissage (le compte collaborateur existe déjà, on l'ACTIVE).
  sessionStorage.setItem('bmci-enroll-email', email.value.trim())
  toast('E-mail vérifié · activons votre compte', 'info')
  router.push({ name: 'otp' })
}
</script>

<template>
  <AuthCard>
    <AuthStepper :active="0" />
    <h1 class="font-display text-xl font-bold text-ink">Activez votre compte BMCI</h1>
    <p class="mt-1 text-sm text-ink-3">
      Votre compte collaborateur existe déjà dans l'annuaire du Groupe. Activez-le avec votre
      e-mail professionnel <b>@bmci.local</b> — vos informations RH seront pré-remplies.
    </p>

    <div class="mt-5 space-y-4">
      <div>
        <label for="ins-name" class="mb-1 block text-xs font-semibold text-ink-2">Nom complet</label>
        <div
          class="flex items-center gap-2 rounded-xl border border-border bg-paper px-3 focus-within:border-green-line"
        >
          <User :size="16" class="text-ink-3" />
          <input
            id="ins-name"
            v-model="name"
            placeholder="Prénom Nom"
            class="w-full bg-transparent py-2.5 text-sm text-ink outline-none"
          />
        </div>
      </div>

      <div>
        <label for="ins-email" class="mb-1 block text-xs font-semibold text-ink-2">E-mail professionnel</label>
        <div
          class="flex items-center gap-2 rounded-xl border bg-paper px-3"
          :class="email && !emailValid ? 'border-danger/50' : emailValid ? 'border-green-line' : 'border-border'"
        >
          <Mail :size="16" class="text-ink-3" />
          <input
            id="ins-email"
            v-model="email"
            type="email"
            placeholder="prenom.nom@bmci.local"
            class="w-full bg-transparent py-2.5 text-sm text-ink outline-none"
          />
          <Check v-if="emailValid" :size="16" class="text-green-deep" />
        </div>
        <p v-if="email && !emailValid" class="mt-1 text-[11px] text-danger">
          Format attendu : prenom.nom@bmci.local
        </p>
      </div>

      <div>
        <label for="ins-password" class="mb-1 block text-xs font-semibold text-ink-2">Mot de passe</label>
        <div
          class="flex items-center gap-2 rounded-xl border border-border bg-paper px-3 focus-within:border-green-line"
        >
          <Lock :size="16" class="text-ink-3" />
          <input
            id="ins-password"
            v-model="password"
            :type="showPwd ? 'text' : 'password'"
            placeholder="Créez un mot de passe robuste"
            class="w-full bg-transparent py-2.5 text-sm text-ink outline-none"
          />
          <button
            type="button"
            class="text-ink-3 hover:text-ink"
            :aria-label="showPwd ? 'Masquer le mot de passe' : 'Afficher le mot de passe'"
            @click="showPwd = !showPwd"
          >
            <component :is="showPwd ? EyeOff : Eye" :size="16" />
          </button>
        </div>
        <div class="mt-2 h-1.5 overflow-hidden rounded-full bg-panel-2">
          <div
            class="h-full rounded-full transition-all"
            :class="strengthColor"
            :style="{ width: (strength / 5) * 100 + '%' }"
          />
        </div>
        <p
          v-if="password"
          class="mt-1 text-[11px] font-medium"
          :class="pwdValid ? 'text-green-deep' : 'text-ink-3'"
        >
          Force : {{ strengthLabel }}
        </p>
        <ul class="mt-2 grid grid-cols-2 gap-1">
          <li
            v-for="[k, lab] in critList"
            :key="k"
            class="flex items-center gap-1 text-[11px]"
            :class="criteria[k] ? 'text-green-deep' : 'text-ink-3'"
          >
            <Check :size="12" :class="criteria[k] ? 'opacity-100' : 'opacity-30'" /> {{ lab }}
          </li>
        </ul>
      </div>

      <BaseButton block :disabled="!canSubmit" @click="submit">
        <Check :size="16" /> Activer mon compte
      </BaseButton>
      <p class="text-center text-xs text-ink-3">
        Déjà un compte ?
        <button
          class="font-semibold text-green-deep hover:underline"
          @click="router.push({ name: 'connexion' })"
        >
          Se connecter
        </button>
      </p>
    </div>
  </AuthCard>
</template>
