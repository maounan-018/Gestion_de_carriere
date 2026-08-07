<script setup lang="ts">
/**
 * Avis (revue par les pairs) d'un profil + dépôt d'un avis. Le droit d'écrire
 * (peutNoter) vient du backend : un utilisateur ne peut noter que SON ÉQUIPE
 * (subordonnés directs, coéquipiers de même manager) et son MANAGER DIRECT.
 * Réutilisable : profil public (collaborateur), fiche manager, fiche HRBP.
 */
import { ref, onMounted, watch } from 'vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { PeerReview } from '@/types/domain'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseAvatar from '@/components/ui/BaseAvatar.vue'
import BaseButton from '@/components/ui/BaseButton.vue'

const props = defineProps<{ profilId: string; who?: string }>()
const { toast } = useToast()

const avis = ref<PeerReview[]>([])
const peutNoter = ref(false)
const loading = ref(true)
const etoiles = ref(5)
const texte = ref('')
const saving = ref(false)

const stars = (n: number) => '★★★★★'.slice(0, n) + '☆☆☆☆☆'.slice(0, 5 - n)

async function load() {
  loading.value = true
  try {
    const r = await apiService.getAvis(props.profilId)
    avis.value = r.avis
    peutNoter.value = r.peutNoter
  } catch {
    avis.value = []
    peutNoter.value = false
  } finally {
    loading.value = false
  }
}
onMounted(load)
watch(() => props.profilId, load)

async function submit() {
  const t = texte.value.trim()
  if (t.length < 3 || saving.value) return
  saving.value = true
  try {
    await apiService.creerAvis(props.profilId, t, etoiles.value)
    texte.value = ''
    etoiles.value = 5
    toast('Avis enregistré', 'ok')
    await load()
  } catch (e) {
    toast(e instanceof Error ? e.message : "Échec de l'enregistrement", 'error')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <BaseCard title="Avis des pairs">
    <div v-if="loading" class="py-3 text-sm text-ink-3">Chargement des avis…</div>
    <template v-else>
      <div v-if="avis.length" class="space-y-3">
        <div v-for="(r, i) in avis" :key="i" class="flex gap-3">
          <BaseAvatar :initials="r.initials" size="md" :seed="`avis-${i}`" />
          <div class="min-w-0 flex-1">
            <p class="text-xs text-ink-3">
              <span class="text-gold">{{ stars(r.stars) }}</span>
              <b class="text-ink-2"> {{ r.name }}</b><span v-if="r.role"> · {{ r.role }}</span>
            </p>
            <p class="text-sm text-ink-2">{{ r.text }}</p>
          </div>
        </div>
      </div>
      <p v-else class="text-sm text-ink-3">Aucun avis pour le moment.</p>

      <!-- Dépôt d'un avis : uniquement si autorisé (équipe / manager direct). -->
      <div v-if="peutNoter" class="mt-4 border-t border-border pt-3">
        <p class="mb-2 text-xs font-semibold text-ink-2">
          Laisser un avis{{ who ? ` sur ${who}` : '' }}
        </p>
        <div class="mb-2 flex items-center gap-1" role="radiogroup" aria-label="Note sur 5">
          <button
            v-for="n in 5"
            :key="n"
            type="button"
            class="text-xl leading-none transition"
            :class="n <= etoiles ? 'text-gold' : 'text-border-strong hover:text-gold/60'"
            :aria-label="`${n} étoile${n > 1 ? 's' : ''}`"
            @click="etoiles = n"
          >★</button>
          <span class="ml-1 text-xs text-ink-3">{{ etoiles }}/5</span>
        </div>
        <textarea
          v-model="texte"
          rows="3"
          maxlength="800"
          placeholder="Votre retour : points forts, collaboration, axes d'amélioration…"
          class="w-full rounded-xl border border-border bg-panel px-3 py-2 text-sm text-ink outline-none focus:border-green-line"
        />
        <div class="mt-2 flex justify-end">
          <BaseButton size="sm" :disabled="saving || texte.trim().length < 3" @click="submit">
            {{ saving ? 'Envoi…' : 'Publier l\'avis' }}
          </BaseButton>
        </div>
      </div>
    </template>
  </BaseCard>
</template>
