<script setup lang="ts">
/**
 * CoachDocsAttach — Trombone + popover pour les documents personnels du Coach.
 *
 * Place le trombone 📎 dans la barre d'entrée du chat : clic → file picker →
 * upload (apiService.uploadCoachDocument) → toast de confirmation. Un petit
 * badge « N docs » cliquable ouvre un popover listant les documents indexés,
 * avec suppression unitaire. Les documents sont scopés sur l'utilisateur côté
 * backend ; cette UI ne fait que les afficher et les gérer.
 */
import { ref, onMounted, computed } from 'vue'
import { Paperclip, X, FileText, Loader2 } from '@lucide/vue'
import { apiService, type CoachDocumentItem } from '@/services/apiService'
import { ApiError } from '@/services/http'

const docs = ref<CoachDocumentItem[]>([])
const open = ref(false)        // popover ouvert
const uploading = ref(false)
const removingId = ref<number | null>(null)
const error = ref<string | null>(null)
const notice = ref<string | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)

const count = computed(() => docs.value.length)

async function load() {
  try {
    docs.value = await apiService.listCoachDocuments()
  } catch {
    docs.value = []  // RAG indisponible : on n'affiche rien plutôt que planter l'UI
  }
}
onMounted(load)

function pick() {
  error.value = null
  notice.value = null
  fileInput.value?.click()
}

async function onFile(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''                      // permet de re-sélectionner le même fichier
  if (!file) return
  uploading.value = true
  error.value = null
  try {
    const doc = await apiService.uploadCoachDocument(file)
    docs.value = [doc, ...docs.value]
    notice.value = `« ${doc.filename} » indexé (${doc.chunk_count} fragment${doc.chunk_count > 1 ? 's' : ''}).`
    open.value = true                   // ouvre la liste pour montrer le résultat
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : "Échec du téléversement."
  } finally {
    uploading.value = false
  }
}

async function remove(doc: CoachDocumentItem) {
  if (!confirm(`Supprimer « ${doc.filename} » ? Le Coach ne pourra plus s'en servir.`)) return
  removingId.value = doc.id
  try {
    await apiService.deleteCoachDocument(doc.id)
    docs.value = docs.value.filter((d) => d.id !== doc.id)
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : "Échec de la suppression."
  } finally {
    removingId.value = null
  }
}

function formatSize(b: number): string {
  if (b < 1024) return `${b} o`
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(0)} Ko`
  return `${(b / 1024 / 1024).toFixed(1)} Mo`
}
</script>

<template>
  <div class="relative flex items-center gap-1">
    <!-- Trombone : ouvre le file picker (upload direct). -->
    <button
      type="button"
      :disabled="uploading"
      :title="uploading ? 'Indexation en cours…' : 'Téléverser un document (PDF, Word, Excel, texte)'"
      class="inline-flex items-center gap-1 rounded-lg p-1.5 text-ink-3 transition hover:bg-green-ghost hover:text-green-deep disabled:opacity-50"
      @click="pick"
    >
      <Loader2 v-if="uploading" :size="16" class="animate-spin" />
      <Paperclip v-else :size="16" />
    </button>

    <!-- Badge compteur : ouvre/ferme le popover. Masqué si zéro document. -->
    <button
      v-if="count > 0"
      type="button"
      :title="`${count} document${count > 1 ? 's' : ''} personnel${count > 1 ? 's' : ''}`"
      class="rounded-full border border-green-line bg-green-ghost px-2 py-0.5 text-[11px] font-semibold text-green-deep transition hover:bg-green-wash"
      @click="open = !open"
    >
      {{ count }} doc{{ count > 1 ? 's' : '' }}
    </button>

    <input ref="fileInput" type="file" class="hidden"
           accept=".pdf,.docx,.xlsx,.txt,.md" @change="onFile" />

    <!-- Popover : liste des documents + suppression (ancré au bouton, ouvre vers le haut). -->
    <div
      v-if="open"
      class="absolute bottom-full right-0 z-20 mb-2 w-80 rounded-xl border border-border bg-paper p-3 shadow-card"
    >
      <div class="mb-2 flex items-center justify-between">
        <div class="text-xs font-semibold uppercase text-ink-3">Mes documents</div>
        <button
          type="button"
          class="rounded p-0.5 text-ink-3 hover:bg-green-ghost hover:text-green-deep"
          @click="open = false"
        >
          <X :size="14" />
        </button>
      </div>
      <ul v-if="docs.length" class="max-h-72 space-y-1.5 overflow-y-auto">
        <li
          v-for="d in docs"
          :key="d.id"
          class="flex items-center gap-2 rounded-lg bg-green-ghost/50 px-2 py-1.5"
        >
          <FileText :size="14" class="shrink-0 text-green-deep" />
          <div class="min-w-0 flex-1">
            <div class="truncate text-xs font-medium text-ink">{{ d.filename }}</div>
            <div class="text-[10px] text-ink-3">
              {{ d.chunk_count }} fragment{{ d.chunk_count > 1 ? 's' : '' }} ·
              {{ formatSize(d.size_bytes) }}
            </div>
          </div>
          <button
            type="button"
            :disabled="removingId === d.id"
            title="Supprimer"
            class="rounded p-1 text-ink-3 hover:bg-red-50 hover:text-red-600 disabled:opacity-50"
            @click="remove(d)"
          >
            <Loader2 v-if="removingId === d.id" :size="14" class="animate-spin" />
            <X v-else :size="14" />
          </button>
        </li>
      </ul>
      <p v-else class="text-xs text-ink-3">
        Aucun document pour l'instant. Cliquez sur l'icône <Paperclip :size="12" class="inline" />
        pour en ajouter un (PDF, Word, Excel, texte).
      </p>
    </div>

    <!-- Toast d'erreur / confirmation (court, non bloquant). -->
    <div
      v-if="error"
      class="absolute bottom-full right-0 z-30 mb-2 max-w-[260px] rounded-lg bg-red-50 px-2 py-1 text-[11px] text-red-700 shadow"
      @click="error = null"
    >
      {{ error }}
    </div>
    <div
      v-else-if="notice && !open"
      class="absolute bottom-full right-0 z-30 mb-2 max-w-[260px] rounded-lg bg-green-ghost px-2 py-1 text-[11px] text-green-deep shadow"
      @click="notice = null"
    >
      {{ notice }}
    </div>
  </div>
</template>
