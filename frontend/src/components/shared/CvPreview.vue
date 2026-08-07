<script setup lang="ts">
/**
 * Visionneuse de CV intégrée : le PDF est téléchargé en Blob AUTHENTIFIÉ (via
 * apiService.cvBlob → en-tête Bearer en cross-origin, cookie en same-origin) puis
 * affiché dans une iframe via un object URL. Une `<iframe src>` ou un `<a href>`
 * ne peut pas porter d'en-tête d'auth ni contourner `frame-ancestors` du backend :
 * passer par le Blob règle les deux (l'object URL est de la même origine que l'app).
 * Un bouton « Télécharger » réutilise le même object URL.
 */
import { ref, watch, onUnmounted } from 'vue'
import { X, Download } from '@lucide/vue'
import { apiService } from '@/services/apiService'

const props = defineProps<{ modelValue: boolean; profilId: number | null; nom?: string }>()
const emit = defineEmits<{ 'update:modelValue': [boolean] }>()

const objectUrl = ref('')
const loading = ref(false)
const error = ref('')

const downloadName = () =>
  `cv-${(props.nom || 'profil').trim().replace(/\s+/g, '-').toLowerCase() || 'profil'}.pdf`

function revoke() {
  if (objectUrl.value) {
    URL.revokeObjectURL(objectUrl.value)
    objectUrl.value = ''
  }
}

async function load() {
  if (props.profilId == null) return
  revoke()
  error.value = ''
  loading.value = true
  const id = props.profilId
  try {
    const blob = await apiService.cvBlob(id)
    // Le profil a pu changer pendant le téléchargement : on ignore une réponse obsolète.
    if (id !== props.profilId) return
    objectUrl.value = URL.createObjectURL(blob)
  } catch (e) {
    error.value = (e as Error)?.message || 'CV indisponible.'
  } finally {
    if (id === props.profilId) loading.value = false
  }
}

function close() {
  emit('update:modelValue', false)
}
function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') close()
}
watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      load()
      document.addEventListener('keydown', onKey)
    } else {
      document.removeEventListener('keydown', onKey)
      revoke()
    }
  },
)
onUnmounted(() => {
  document.removeEventListener('keydown', onKey)
  revoke()
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="modelValue && profilId != null"
      class="modal-in fixed inset-0 z-50 grid place-items-center bg-ink/40 p-4 backdrop-blur-sm"
      @click.self="close"
    >
      <div
        class="flex h-[88vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl border border-border bg-paper shadow-float"
        role="dialog"
        aria-modal="true"
      >
        <div class="flex items-center justify-between gap-3 border-b border-border px-5 py-3">
          <h3 class="min-w-0 truncate font-display text-lg font-bold text-ink">
            CV<span v-if="nom"> · {{ nom }}</span>
          </h3>
          <div class="flex shrink-0 items-center gap-2">
            <a
              v-if="objectUrl"
              :href="objectUrl"
              :download="downloadName()"
              class="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs font-semibold text-green-deep hover:bg-green-soft"
            >
              <Download :size="14" /> Télécharger
            </a>
            <button
              class="grid h-8 w-8 place-items-center rounded-lg text-ink-3 hover:bg-panel-2 hover:text-ink"
              aria-label="Fermer"
              @click="close"
            >
              <X :size="18" />
            </button>
          </div>
        </div>
        <div class="relative min-h-0 flex-1 bg-panel-2">
          <iframe
            v-if="objectUrl"
            :src="objectUrl"
            title="Aperçu du CV"
            class="h-full w-full"
          />
          <div
            v-else
            class="grid h-full w-full place-items-center px-6 text-center text-sm text-ink-3"
          >
            <span v-if="loading">Chargement du CV…</span>
            <span v-else-if="error">{{ error }}</span>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.modal-in {
  animation: modalIn 0.18s ease-out;
}
@keyframes modalIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
@media (prefers-reduced-motion: reduce) {
  .modal-in {
    animation: none;
  }
}
</style>
