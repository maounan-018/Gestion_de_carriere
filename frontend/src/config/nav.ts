import {
  Home,
  User as UserIcon,
  Route,
  MessageSquare,
  Briefcase,
  BookOpen,
  Search,
  Sparkles,
  Users,
  Bell,
  Award,
  LayoutGrid,
  Settings,
} from '@lucide/vue'
import type { NavItem } from '@/types/ui'
import type { Role } from '@/types/domain'

/**
 * Navigation par rôle. Les `name` sont les noms de route (préfixés par rôle pour
 * éviter les collisions : reco/entretien/offres/coach existent chez plusieurs rôles).
 * Le router génère les routes à partir de cette config.
 */
export const NAV_CONFIG: Record<Role, NavItem[]> = {
  collab: [
    { name: 'collab.dashboard', label: 'Tableau de bord', icon: Home },
    { name: 'collab.profil', label: 'Mon profil', icon: UserIcon },
    { name: 'collab.reco', label: 'Recommandations', icon: Route },
    { name: 'collab.entretien', label: 'Entretiens', icon: MessageSquare },
    { name: 'collab.offres', label: 'Offres internes', icon: Briefcase },
    { name: 'collab.formation', label: 'Formations', icon: BookOpen },
    { name: 'collab.recherche', label: 'Rechercher', icon: Search },
    { name: 'collab.coach', label: 'Coach Carrière', icon: Sparkles },
  ],
  manager: [
    { name: 'manager.dashboard', label: 'Tableau de bord', icon: Home },
    { name: 'manager.equipe', label: 'Mon équipe', icon: Users },
    { name: 'manager.profil', label: 'Mon profil', icon: UserIcon },
    { name: 'manager.reco', label: 'Recommandations', icon: Route },
    { name: 'manager.entretien', label: 'Entretiens', icon: MessageSquare },
    { name: 'manager.offres', label: 'Offres internes', icon: Briefcase },
    { name: 'manager.coach', label: 'Coach Carrière', icon: Sparkles },
  ],
  rh: [
    { name: 'rh.dashboard', label: 'Tableau de bord', icon: Home },
    { name: 'rh.alertes', label: 'Alertes & actions', icon: Bell },
    { name: 'rh.hautsPotentiels', label: 'Hauts potentiels', icon: Award },
    { name: 'rh.cartographie', label: 'Cartographie', icon: LayoutGrid },
    { name: 'rh.entretiens', label: 'Entretiens', icon: MessageSquare },
    { name: 'rh.offres', label: 'Offres internes', icon: Briefcase },
    { name: 'rh.annuaire', label: 'Annuaire', icon: Users },
    { name: 'rh.espace', label: 'Mon espace', icon: UserIcon },
    { name: 'rh.supervision', label: 'Supervision', icon: Settings },
    { name: 'rh.coach', label: 'Coach Carrière', icon: Sparkles },
  ],
}
