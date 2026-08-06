<script setup lang="ts">
/**
 * Visionneuse de CV intégrée à la plateforme : aperçu direct du PDF dans une
 * iframe (le backend le sert en `inline`), sans obliger au téléchargement.
 * Un bouton « Télécharger » reste disponible (attribut download → sauvegarde).
 */
import { ref, computed, watch, onUnmounted } from 'vue'
import { X, Download } from '@lucide/vue'
import { apiService } from '@/services/apiService'

const props = defineProps<{ modelValue: boolean; profilId: number | null; nom?: string }>()
const emit = defineEmits<{ 'update:modelValue': [boolean] }>()

const url = computed(() => (props.profilId != null ? apiService.cvUrl(props.profilId) : ''))
// L'iframe est anti-cache : le cache HTTP peut resservir une ancienne réponse
// (ex. en-têtes de framing obsolètes) et bloquer l'aperçu. Régénéré à l'ouverture.
const bust = ref(Date.now())
const iframeUrl = computed(() => (url.value ? `${url.value}?t=${bust.value}` : ''))

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
      bust.value = Date.now()
      document.addEventListener('keydown', onKey)
    } else {
      document.removeEventListener('keydown', onKey)
    }
  },
)
onUnmounted(() => document.removeEventListener('keydown', onKey))
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
              :href="url"
              download
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
        <iframe
          :src="iframeUrl"
          title="Aperçu du CV"
          class="min-h-0 flex-1 w-full bg-panel-2"
        />
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
