<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Flag, Mail, LayoutGrid, Briefcase } from '@lucide/vue'
import { useToast } from '@/composables/useToast'
import AuthCard from '@/components/access/AuthCard.vue'
import AuthStepper from '@/components/access/AuthStepper.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'

const router = useRouter()
const { toast } = useToast()
</script>

<template>
  <AuthCard>
    <AuthStepper :active="2" />
    <div class="flex items-start gap-3 rounded-xl border border-warning/30 bg-warning-soft/50 p-3">
      <Flag :size="18" class="mt-0.5 shrink-0 text-warning" />
      <div>
        <div class="text-sm font-bold text-ink">Incohérence détectée dans l'annuaire</div>
        <p class="mt-0.5 text-xs text-ink-2">
          L'entité et le poste sélectionnés ne correspondent pas à votre e-mail dans l'annuaire
          BMCI. Corrigez l'étape, ou contactez les RH si votre rattachement vient de changer.
        </p>
      </div>
    </div>

    <h1 class="mt-4 font-display text-lg font-bold text-ink">Vérifions vos informations</h1>
    <div class="mt-3 space-y-2">
      <div
        class="flex items-center justify-between rounded-lg border border-border bg-panel px-3 py-2 text-sm"
      >
        <span class="flex items-center gap-2 text-ink-3"><Mail :size="14" /> E-mail</span>
        <span class="font-medium text-ink">youssef.elamrani@bmci.local</span>
      </div>
      <div
        class="flex items-center justify-between rounded-lg border border-border bg-panel px-3 py-2 text-sm"
      >
        <span class="flex items-center gap-2 text-ink-3"><LayoutGrid :size="14" /> Entité déclarée</span>
        <span class="flex items-center gap-2 font-medium text-ink">
          IT &amp; Digital <BasePill tone="warn">à vérifier</BasePill>
        </span>
      </div>
      <div
        class="flex items-center justify-between rounded-lg border border-border bg-panel px-3 py-2 text-sm"
      >
        <span class="flex items-center gap-2 text-ink-3"><Briefcase :size="14" /> Poste déclaré</span>
        <span class="flex items-center gap-2 font-medium text-ink">
          Chef de projet <BasePill tone="warn">à vérifier</BasePill>
        </span>
      </div>
    </div>

    <BaseButton block class="mt-4" @click="router.push({ name: 'onboarding' })">
      Refaire cette étape
    </BaseButton>
    <BaseButton
      block
      variant="secondary"
      class="mt-2"
      @click="toast('Demande transmise au support RH', 'info')"
    >
      Contacter le support RH
    </BaseButton>
  </AuthCard>
</template>
