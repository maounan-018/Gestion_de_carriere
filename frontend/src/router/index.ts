import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useSessionStore } from '@/stores/session'
import { NAV_CONFIG } from '@/config/nav'
import type { Role } from '@/types/domain'
import AppShell from '@/components/layout/AppShell.vue'

// Écrans applicatifs générés depuis la config de navigation. Les écrans déjà
// implémentés (M3+) renvoient leur vue, les autres un placeholder. Chaque route
// est protégée par son rôle (RBAC).
function viewFor(name: string) {
  switch (name) {
    case 'collab.dashboard':
      return () => import('@/views/collab/DashboardView.vue')
    case 'collab.profil':
      return () => import('@/views/collab/ProfilView.vue')
    case 'collab.reco':
      return () => import('@/views/collab/RecoView.vue')
    case 'collab.entretien':
      return () => import('@/views/collab/EntretienView.vue')
    case 'collab.offres':
      return () => import('@/views/collab/OffresView.vue')
    case 'collab.formation':
      return () => import('@/views/collab/FormationsView.vue')
    case 'collab.recherche':
      return () => import('@/views/collab/RechercheView.vue')
    case 'collab.coach':
      return () => import('@/views/collab/CoachView.vue')
    case 'manager.dashboard':
      return () => import('@/views/manager/DashboardView.vue')
    case 'manager.equipe':
      return () => import('@/views/manager/EquipeView.vue')
    case 'manager.profil':
      return () => import('@/views/manager/ProfilView.vue')
    case 'manager.reco':
      // Reco manager = MÊME écran que le collaborateur (vue partagée, role-aware).
      return () => import('@/views/collab/RecoView.vue')
    case 'manager.entretien':
      return () => import('@/views/manager/EntretienView.vue')
    case 'manager.offres':
      return () => import('@/views/manager/OffresView.vue')
    case 'manager.coach':
      return () => import('@/views/manager/CoachView.vue')
    case 'rh.dashboard':
      return () => import('@/views/rh/DashboardView.vue')
    case 'rh.alertes':
      return () => import('@/views/rh/AlertesView.vue')
    case 'rh.hautsPotentiels':
      return () => import('@/views/rh/HautsPotentielsView.vue')
    case 'rh.cartographie':
      return () => import('@/views/rh/CartographieView.vue')
    case 'rh.entretiens':
      return () => import('@/views/rh/EntretiensView.vue')
    case 'rh.offres':
      return () => import('@/views/rh/OffresView.vue')
    case 'rh.annuaire':
      return () => import('@/views/rh/AnnuaireView.vue')
    case 'rh.espace':
      return () => import('@/views/rh/EspaceView.vue')
    case 'rh.supervision':
      return () => import('@/views/rh/SupervisionView.vue')
    case 'rh.coach':
      return () => import('@/views/rh/CoachView.vue')
    case 'rh.besoins':
      return () => import('@/views/rh/BesoinsRhView.vue')
    case 'rh.souhaitsRecus':
      return () => import('@/views/rh/MobilitesRhView.vue')
    default:
      return () => import('@/views/Placeholder.vue')
  }
}

const appChildren: RouteRecordRaw[] = (Object.keys(NAV_CONFIG) as Role[]).flatMap((role) =>
  NAV_CONFIG[role].map((item) => ({
    path: `${role}/${item.name.split('.')[1]}`,
    name: item.name,
    component: viewFor(item.name),
    meta: { roles: [role], title: item.label },
  })),
)

// Écrans de détail hors navigation (collab).
const collabDetailRoutes: RouteRecordRaw[] = [
  {
    path: 'collab/offre/:key',
    name: 'collab.offreDetail',
    component: () => import('@/views/collab/OffreDetailView.vue'),
    meta: { roles: ['collab'], title: "Détail de l'offre" },
  },
  {
    path: 'collab/candidatures',
    name: 'collab.mesCandidatures',
    component: () => import('@/views/collab/MesCandidaturesView.vue'),
    meta: { roles: ['collab'], title: 'Mes candidatures' },
  },
  {
    path: 'collab/notifications',
    name: 'collab.notifications',
    component: () => import('@/views/collab/NotificationsView.vue'),
    meta: { roles: ['collab'], title: 'Notifications' },
  },
  {
    path: 'collab/souhaits',
    name: 'collab.souhaits',
    component: () => import('@/views/collab/SouhaitsView.vue'),
    meta: { roles: ['collab'], title: "Mes demandes d'évolution" },
  },
  {
    path: 'collab/mon-profil/editer',
    name: 'collab.editProfil',
    component: () => import('@/views/collab/EditProfilView.vue'),
    meta: { roles: ['collab'], title: 'Éditer mon profil' },
  },
  {
    // Écran dédié « Éditer mon profil » partagé (même vue) pour le manager et la HRBP.
    path: 'manager/mon-profil/editer',
    name: 'manager.editProfil',
    component: () => import('@/views/collab/EditProfilView.vue'),
    meta: { roles: ['manager'], title: 'Éditer mon profil' },
  },
  {
    path: 'rh/mon-profil/editer',
    name: 'rh.editProfil',
    component: () => import('@/views/collab/EditProfilView.vue'),
    meta: { roles: ['rh'], title: 'Éditer mon profil' },
  },
  {
    // Sous-écrans reco PARTAGÉS avec le manager (vues collab réutilisées, role-aware).
    path: 'manager/formation',
    name: 'manager.formation',
    component: () => import('@/views/collab/FormationsView.vue'),
    meta: { roles: ['manager'], title: 'Formations' },
  },
  {
    path: 'manager/passerelles',
    name: 'manager.passerelles',
    component: () => import('@/views/collab/PasserellesView.vue'),
    meta: { roles: ['manager'], title: 'Passerelles métiers' },
  },
  {
    path: 'manager/passerelle/:metier',
    name: 'manager.passerelleDetail',
    component: () => import('@/views/collab/PasserelleDetailView.vue'),
    meta: { roles: ['manager'], title: 'Passerelle métier' },
  },
  {
    path: 'collab/passerelles',
    name: 'collab.passerelles',
    component: () => import('@/views/collab/PasserellesView.vue'),
    meta: { roles: ['collab'], title: 'Passerelles métiers' },
  },
  {
    path: 'collab/passerelle/:metier',
    name: 'collab.passerelleDetail',
    component: () => import('@/views/collab/PasserelleDetailView.vue'),
    meta: { roles: ['collab'], title: 'Passerelle métier' },
  },
  {
    path: 'collab/collegue/:id',
    name: 'collab.profilPublic',
    component: () => import('@/views/collab/ProfilPublicView.vue'),
    meta: { roles: ['collab'], title: 'Profil public' },
  },
]

// Écrans de détail hors navigation (manager).
const managerDetailRoutes: RouteRecordRaw[] = [
  {
    path: 'manager/collaborateur/:id',
    name: 'manager.ficheCollab',
    component: () => import('@/views/manager/FicheCollabView.vue'),
    meta: { roles: ['manager'], title: 'Fiche collaborateur' },
  },
  {
    path: 'manager/souhaits-recus',
    name: 'manager.souhaitsRecus',
    component: () => import('@/views/manager/SouhaitsRecusView.vue'),
    meta: { roles: ['manager'], title: "Demandes d'évolution reçues" },
  },
  {
    path: 'manager/mes-offres',
    name: 'manager.mesOffres',
    component: () => import('@/views/manager/MesOffresView.vue'),
    meta: { roles: ['manager'], title: 'Mes offres publiées' },
  },
  {
    path: 'manager/candidatures-actives',
    name: 'manager.candidaturesActives',
    component: () => import('@/views/manager/CandidaturesActivesView.vue'),
    meta: { roles: ['manager'], title: 'Candidatures · offres en cours' },
  },
  {
    path: 'manager/poste/:key/profils',
    name: 'manager.profilsCompatibles',
    component: () => import('@/views/manager/ProfilsCompatiblesView.vue'),
    meta: { roles: ['manager'], title: 'Profils recommandés' },
  },
  {
    path: 'manager/offre/:key',
    name: 'manager.offreDetail',
    component: () => import('@/views/manager/OffreDetailView.vue'),
    meta: { roles: ['manager'], title: "Détail de l'offre" },
  },
  {
    // Revue des candidats d'une offre PUBLIÉE par le manager (au lieu de « postuler »).
    path: 'manager/mes-offres/:key/candidats',
    name: 'manager.revueCandidats',
    component: () => import('@/views/rh/RevueCandidatsView.vue'),
    meta: { roles: ['manager'], title: 'Candidats de mon offre' },
  },
  {
    path: 'manager/offre/:key/evaluation',
    name: 'manager.evaluationMission',
    component: () => import('@/views/manager/EvaluationMissionView.vue'),
    meta: { roles: ['manager'], title: 'Évaluation de mission' },
  },
  {
    path: 'manager/notifications',
    name: 'manager.notifications',
    component: () => import('@/views/manager/NotificationsView.vue'),
    meta: { roles: ['manager'], title: 'Notifications' },
  },
]

// Écrans de détail hors navigation (RH).
const rhDetailRoutes: RouteRecordRaw[] = [
  {
    path: 'rh/besoin/:id',
    name: 'rh.besoinDetail',
    component: () => import('@/views/rh/BesoinDetailRhView.vue'),
    meta: { roles: ['rh'], title: 'Détail du besoin' },
  },
  {
    path: 'rh/collaborateur/:id',
    name: 'rh.ficheCollabRh',
    component: () => import('@/views/rh/FicheCollabRhView.vue'),
    meta: { roles: ['rh'], title: 'Base de connaissance collaborateur' },
  },
  {
    path: 'rh/bilan/:id',
    name: 'rh.bilan',
    component: () => import('@/views/rh/BilanView.vue'),
    meta: { roles: ['rh'], title: 'Préparer un entretien' },
  },
  {
    path: 'rh/retention',
    name: 'rh.retention',
    component: () => import('@/views/rh/RetentionView.vue'),
    meta: { roles: ['rh'], title: 'Analyse du risque de départ' },
  },
  {
    path: 'rh/cartographie/:pole',
    name: 'rh.cartoDetail',
    component: () => import('@/views/rh/CartoDetailView.vue'),
    meta: { roles: ['rh'], title: 'Cartographie · pôle' },
  },
  {
    path: 'rh/cartographie-plein',
    name: 'rh.cartoPlein',
    component: () => import('@/views/rh/CartoPleinView.vue'),
    meta: { roles: ['rh'], title: 'Cartographie · vue plein écran' },
  },
  {
    path: 'rh/notifications',
    name: 'rh.notifications',
    component: () => import('@/views/rh/NotificationsView.vue'),
    meta: { roles: ['rh'], title: 'Notifications' },
  },
  {
    path: 'rh/offre/:key/candidats',
    name: 'rh.revueCandidats',
    component: () => import('@/views/rh/RevueCandidatsView.vue'),
    meta: { roles: ['rh'], title: 'Revue des candidatures' },
  },
  {
    // Drill-down du KPI « Offres publiées » (HRBP) — vues partagées avec le manager.
    path: 'rh/mes-offres',
    name: 'rh.mesOffres',
    component: () => import('@/views/manager/MesOffresView.vue'),
    meta: { roles: ['rh'], title: 'Mes offres publiées' },
  },
  {
    path: 'rh/candidatures-actives',
    name: 'rh.candidaturesActives',
    component: () => import('@/views/manager/CandidaturesActivesView.vue'),
    meta: { roles: ['rh'], title: 'Candidatures · offres en cours' },
  },
  {
    path: 'rh/referentiel',
    name: 'rh.referentiel',
    component: () => import('@/views/rh/ReferentielView.vue'),
    meta: { roles: ['rh'], title: 'Référentiel & fiches de poste' },
  },
  {
    path: 'rh/mon-entretien',
    name: 'rh.monEntretien',
    component: () => import('@/views/rh/MonEntretienView.vue'),
    meta: { roles: ['rh'], title: 'Mon entretien annuel' },
  },
]

const routes: RouteRecordRaw[] = [
  // --- Accès / Onboarding (public, sans shell — factorisé une seule fois) ---
  { path: '/', name: 'portail', component: () => import('@/views/access/PortailView.vue') },
  {
    path: '/connexion',
    name: 'connexion',
    component: () => import('@/views/access/ConnexionView.vue'),
  },
  {
    path: '/inscription',
    name: 'inscription',
    component: () => import('@/views/access/InscriptionView.vue'),
    meta: { title: 'Créer un compte' },
  },
  {
    path: '/verification',
    name: 'otp',
    component: () => import('@/views/access/OtpView.vue'),
    meta: { title: 'Vérifier votre e-mail' },
  },
  {
    path: '/onboarding',
    name: 'onboarding',
    component: () => import('@/views/access/OnboardingView.vue'),
    meta: { title: 'Configuration du profil' },
  },
  {
    path: '/onboarding/incoherence',
    name: 'onboardingErreur',
    component: () => import('@/views/access/OnboardingErreurView.vue'),
    meta: { title: 'Onboarding · incohérence' },
  },
  {
    path: '/bienvenue',
    name: 'bienvenue',
    component: () => import('@/views/access/BienvenueView.vue'),
    meta: { title: 'Bienvenue' },
  },
  {
    path: '/mot-de-passe-oublie',
    name: 'motDePasseOublie',
    component: () => import('@/views/access/MotDePasseOublieView.vue'),
    meta: { title: 'Mot de passe oublié' },
  },

  // --- Erreurs transverses (G14) ---
  {
    path: '/acces-refuse',
    name: 'accessDenied',
    component: () => import('@/views/AccessDeniedView.vue'),
  },

  // --- Mentions légales & attributions (G16, public) ---
  {
    path: '/mentions-legales',
    name: 'mentionsLegales',
    component: () => import('@/views/MentionsLegalesView.vue'),
    meta: { title: 'Mentions légales & crédits' },
  },

  // --- Espace applicatif (protégé, shell role-aware) ---
  {
    path: '/app',
    component: AppShell,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'appRoot',
        redirect: () => {
          const session = useSessionStore()
          return session.role ? { name: `${session.role}.dashboard` } : { name: 'connexion' }
        },
      },
      ...appChildren,
      ...collabDetailRoutes,
      ...managerDetailRoutes,
      ...rhDetailRoutes,
      // Paramètres & confidentialité — partagé par tous les rôles (G15/G20).
      {
        path: 'parametres',
        name: 'parametres',
        component: () => import('@/views/ParametresView.vue'),
        meta: { title: 'Paramètres & confidentialité' },
      },
    ],
  },

  // --- Dev : maquettes des jalons précédents ---
  { path: '/m0', name: 'm0', component: () => import('@/views/M0Showcase.vue') },
  { path: '/composants', name: 'composants', component: () => import('@/views/M1Showcase.vue') },

  // --- 404 ---
  {
    path: '/:pathMatch(.*)*',
    name: 'notFound',
    component: () => import('@/views/NotFoundView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

// Guards RBAC (manque G19)
router.beforeEach((to) => {
  const session = useSessionStore()

  const requiresAuth = to.matched.some((r) => r.meta.requiresAuth)
  if (requiresAuth && !session.isAuthenticated) {
    return { name: 'connexion', query: { redirect: to.fullPath } }
  }

  const roles = to.meta.roles as Role[] | undefined
  if (roles && session.role && !roles.includes(session.role)) {
    return { name: 'accessDenied' }
  }

  // NB : on NE redirige PAS un utilisateur déjà connecté hors des pages d'accès
  // (portail / connexion). Le portail reste l'entrée à chaque lancement, et la page
  // de connexion permet de re-choisir un rôle (démo multi-rôles) — une nouvelle
  // connexion remplace simplement la session courante.
  return true
})

export default router
