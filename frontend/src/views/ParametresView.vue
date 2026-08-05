<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '@/stores/session'
import { useToast } from '@/composables/useToast'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseToggle from '@/components/ui/BaseToggle.vue'
import AppIcon from '@/components/ui/AppIcon.vue'

const router = useRouter()
const session = useSessionStore()
const { toast } = useToast()

const visibility = ref({ profil: true, competences: true, avis: false })
const notifs = ref({ offres: true, souhaits: true, entretiens: true, evaluations: true })

// Journal des accès (démo synthétique · traçabilité G20).
const accessLog = [
  { who: 'Nadia Alami', role: 'RH', when: 'Il y a 2 jours', reason: "Préparation d'un entretien RH" },
  { who: 'Jean-Marc Dupont', role: 'Manager', when: 'Il y a 5 jours', reason: "Revue d'équipe" },
]

function save() {
  toast('Préférences enregistrées')
}
async function logout() {
  await session.logout()
  router.push({ name: 'portail' })
}
</script>

<template>
  <div class="space-y-5">
    <div class="grid gap-5 lg:grid-cols-2">
      <BaseCard title="Confidentialité du profil">
        <p class="mb-3 text-xs text-ink-3">
          Choisissez ce que les autres collaborateurs du Groupe peuvent consulter.
        </p>
        <div class="space-y-3">
          <label class="flex cursor-pointer items-center justify-between gap-3">
            <span>
              <b class="text-sm text-ink">Profil</b>
              <small class="block text-ink-3">Poste, description, parcours</small>
            </span>
            <BaseToggle v-model="visibility.profil" />
          </label>
          <label class="flex cursor-pointer items-center justify-between gap-3">
            <span>
              <b class="text-sm text-ink">Compétences</b>
              <small class="block text-ink-3">Niveaux et certifications</small>
            </span>
            <BaseToggle v-model="visibility.competences" />
          </label>
          <label class="flex cursor-pointer items-center justify-between gap-3">
            <span>
              <b class="text-sm text-ink">Avis des pairs</b>
              <small class="block text-ink-3">Retours de vos collègues</small>
            </span>
            <BaseToggle v-model="visibility.avis" />
          </label>
        </div>
        <BaseButton size="sm" class="mt-4" @click="save">Enregistrer</BaseButton>
      </BaseCard>

      <BaseCard title="Préférences de notifications">
        <div class="space-y-3">
          <label class="flex cursor-pointer items-center justify-between gap-3">
            <span class="text-sm text-ink">Nouvelles offres compatibles</span>
            <BaseToggle v-model="notifs.offres" />
          </label>
          <label class="flex cursor-pointer items-center justify-between gap-3">
            <span class="text-sm text-ink">Mes souhaits</span>
            <BaseToggle v-model="notifs.souhaits" />
          </label>
          <label class="flex cursor-pointer items-center justify-between gap-3">
            <span class="text-sm text-ink">Entretiens</span>
            <BaseToggle v-model="notifs.entretiens" />
          </label>
          <label class="flex cursor-pointer items-center justify-between gap-3">
            <span class="text-sm text-ink">Évaluations</span>
            <BaseToggle v-model="notifs.evaluations" />
          </label>
        </div>
        <BaseButton size="sm" class="mt-4" @click="save">Enregistrer</BaseButton>
      </BaseCard>
    </div>

    <BaseCard title="Journal des accès à votre profil">
      <p class="mb-3 text-xs text-ink-3">
        Traçabilité : qui a consulté votre base de connaissance (RH et managers habilités).
      </p>
      <div class="divide-y divide-border">
        <div v-for="(a, i) in accessLog" :key="i" class="flex items-center gap-3 py-2.5">
          <div class="grid h-8 w-8 place-items-center rounded-lg bg-panel-2 text-ink-3">
            <AppIcon name="user" :size="15" />
          </div>
          <div class="min-w-0 flex-1">
            <b class="text-sm text-ink">{{ a.who }}</b>
            <span class="text-xs text-ink-3"> · {{ a.role }}</span>
            <p class="text-xs text-ink-3">{{ a.reason }}</p>
          </div>
          <span class="shrink-0 text-[11px] text-ink-3">{{ a.when }}</span>
        </div>
      </div>
    </BaseCard>

    <BaseCard title="Compte">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div class="text-sm font-bold text-ink">{{ session.user?.name }}</div>
          <div class="text-xs text-ink-3">{{ session.user?.email }} · {{ session.user?.roleLabel }}</div>
        </div>
        <BaseButton variant="secondary" size="sm" @click="logout">
          <AppIcon name="lock" :size="14" /> Se déconnecter
        </BaseButton>
      </div>
      <RouterLink
        :to="{ name: 'mentionsLegales' }"
        class="mt-3 inline-block text-xs text-ink-3 hover:text-green-deep"
      >
        Mentions légales & crédits →
      </RouterLink>
    </BaseCard>
  </div>
</template>
