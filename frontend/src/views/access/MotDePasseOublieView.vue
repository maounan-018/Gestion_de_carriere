<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Mail, Lock, Check, Eye, EyeOff } from '@lucide/vue'
import { useToast } from '@/composables/useToast'
import AuthCard from '@/components/access/AuthCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'

const router = useRouter()
const { toast } = useToast()

const step = ref(0)
const email = ref('')
const emailValid = computed(() => /^[^@\s.]+\.[^@\s]+@bnpparibas\.com$/i.test(email.value.trim()))

const digits = ref<string[]>(['', '', '', '', '', ''])
const inputs = ref<HTMLInputElement[]>([])
const codeComplete = computed(() => digits.value.every((d) => d !== ''))

const pwd = ref('')
const pwd2 = ref('')
const showPwd = ref(false)
const strong = computed(
  () =>
    pwd.value.length >= 8 &&
    /[A-Z]/.test(pwd.value) &&
    /[a-z]/.test(pwd.value) &&
    /\d/.test(pwd.value) &&
    /[^A-Za-z0-9]/.test(pwd.value),
)
const match = computed(() => !!pwd.value && pwd.value === pwd2.value)

function sendCode() {
  if (!emailValid.value) return
  toast('Code envoyé à ' + email.value.trim(), 'info')
  step.value = 1
}
function onInput(i: number, e: Event) {
  const v = (e.target as HTMLInputElement).value.replace(/\D/g, '').slice(0, 1)
  digits.value[i] = v
  if (v && i < 5) inputs.value[i + 1]?.focus()
}
function reset() {
  if (strong.value && match.value) {
    toast('Mot de passe réinitialisé')
    router.push({ name: 'connexion' })
  }
}
</script>

<template>
  <AuthCard>
    <!-- Indicateur d'étapes -->
    <div class="mb-5 flex items-center justify-center gap-1.5">
      <template v-for="i in 3" :key="i">
        <span
          class="grid h-6 w-6 place-items-center rounded-full text-[11px] font-bold"
          :class="
            i - 1 < step
              ? 'bg-green text-white'
              : i - 1 === step
                ? 'border border-green-line bg-green-soft text-green-deep'
                : 'border border-border bg-panel-2 text-ink-3'
          "
        >
          {{ i - 1 < step ? '✓' : i }}
        </span>
        <span v-if="i < 3" class="h-px w-5" :class="i - 1 < step ? 'bg-green' : 'bg-border'" />
      </template>
    </div>

    <!-- Étape 1 : e-mail -->
    <template v-if="step === 0">
      <h1 class="font-display text-xl font-bold text-ink">Mot de passe oublié ?</h1>
      <p class="mt-1 text-sm text-ink-3">
        Saisissez votre e-mail professionnel : nous vous enverrons un code de réinitialisation.
      </p>
      <div class="mt-4">
        <div
          class="flex items-center gap-2 rounded-xl border bg-paper px-3"
          :class="email && !emailValid ? 'border-danger/50' : emailValid ? 'border-green-line' : 'border-border'"
        >
          <Mail :size="16" class="text-ink-3" />
          <input
            v-model="email"
            type="email"
            placeholder="prenom.nom@bnpparibas.com"
            class="w-full bg-transparent py-2.5 text-sm text-ink outline-none"
          />
          <Check v-if="emailValid" :size="16" class="text-green-deep" />
        </div>
      </div>
      <BaseButton block class="mt-4" :disabled="!emailValid" @click="sendCode">
        Envoyer le code →
      </BaseButton>
      <p class="mt-4 text-center text-xs">
        <button class="text-ink-3 hover:text-green-deep" @click="router.push({ name: 'connexion' })">
          ← Retour à la connexion
        </button>
      </p>
    </template>

    <!-- Étape 2 : code -->
    <template v-else-if="step === 1">
      <h1 class="text-center font-display text-xl font-bold text-ink">Entrez le code reçu</h1>
      <p class="mt-1 text-center text-sm text-ink-3">
        Un code à 6 chiffres vient d'être envoyé à votre adresse.
      </p>
      <div class="mt-5 flex justify-center gap-2">
        <input
          v-for="(d, i) in digits"
          :key="i"
          ref="inputs"
          :value="d"
          inputmode="numeric"
          maxlength="1"
          class="h-12 w-11 rounded-xl border border-border bg-paper text-center font-display text-lg font-bold text-ink outline-none focus:border-green-line"
          @input="onInput(i, $event)"
        />
      </div>
      <BaseButton block class="mt-5" :disabled="!codeComplete" @click="step = 2">
        Continuer →
      </BaseButton>
      <p class="mt-4 text-center text-xs text-ink-3">
        Pas reçu ?
        <button
          class="font-semibold text-green-deep hover:underline"
          @click="toast('Nouveau code envoyé', 'info')"
        >
          Renvoyer le code
        </button>
      </p>
    </template>

    <!-- Étape 3 : nouveau mot de passe -->
    <template v-else>
      <h1 class="font-display text-xl font-bold text-ink">Nouveau mot de passe</h1>
      <p class="mt-1 text-sm text-ink-3">Choisissez un mot de passe robuste.</p>
      <div class="mt-4 space-y-3">
        <div
          class="flex items-center gap-2 rounded-xl border border-border bg-paper px-3 focus-within:border-green-line"
        >
          <Lock :size="16" class="text-ink-3" />
          <input
            v-model="pwd"
            :type="showPwd ? 'text' : 'password'"
            placeholder="Nouveau mot de passe"
            class="w-full bg-transparent py-2.5 text-sm text-ink outline-none"
          />
          <button type="button" class="text-ink-3 hover:text-ink" @click="showPwd = !showPwd">
            <component :is="showPwd ? EyeOff : Eye" :size="16" />
          </button>
        </div>
        <div
          class="flex items-center gap-2 rounded-xl border bg-paper px-3"
          :class="pwd2 && !match ? 'border-danger/50' : match ? 'border-green-line' : 'border-border'"
        >
          <Lock :size="16" class="text-ink-3" />
          <input
            v-model="pwd2"
            type="password"
            placeholder="Confirmez le mot de passe"
            class="w-full bg-transparent py-2.5 text-sm text-ink outline-none"
          />
        </div>
        <p v-if="pwd && !strong" class="text-[11px] text-ink-3">
          8 caractères, une majuscule, une minuscule, un chiffre et un caractère spécial.
        </p>
        <p v-else-if="pwd2 && !match" class="text-[11px] text-danger">
          Les mots de passe ne correspondent pas.
        </p>
      </div>
      <BaseButton block class="mt-4" :disabled="!(strong && match)" @click="reset">
        <Check :size="16" /> Réinitialiser mon mot de passe
      </BaseButton>
    </template>
  </AuthCard>
</template>
