import { reactive } from 'vue'
import type { ToastTone } from '@/types/ui'

export interface ToastItem {
  id: number
  message: string
  tone: ToastTone
}

// Singleton réactif partagé par toute l'app (ToastHost lit cette liste).
const state = reactive<{ items: ToastItem[] }>({ items: [] })
let seq = 0

export function useToast() {
  function dismiss(id: number) {
    const i = state.items.findIndex((t) => t.id === id)
    if (i > -1) state.items.splice(i, 1)
  }

  function toast(message: string, tone: ToastTone = 'ok', ms = 2600) {
    const id = ++seq
    state.items.push({ id, message, tone })
    window.setTimeout(() => dismiss(id), ms)
    return id
  }

  return { items: state.items, toast, dismiss }
}
