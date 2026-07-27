import type { Component } from 'vue'
import type { RouteLocationRaw } from 'vue-router'

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'ai' | 'danger'
export type ButtonSize = 'sm' | 'md'
export type ToastTone = 'ok' | 'info' | 'error'

/** Élément de navigation de la sidebar (route-driven). */
export interface NavItem {
  name: string // nom de route (vue-router)
  label: string
  icon: Component // composant lucide
}

/** Élément de fil d'ariane. */
export interface CrumbItem {
  label: string
  to?: RouteLocationRaw
}
