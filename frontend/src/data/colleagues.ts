import type { Colleague } from '@/types/domain'

/** Annuaire des collègues (informations publiques). */
export const COLLEAGUES: Colleague[] = [
  { id: 'aya', initials: 'AB', name: 'Aya El Amrani', role: "Chargée d'Affaires Entreprises", entity: 'Corporate Banking', skills: ['Analyse crédit', 'Anglais financier', 'Négociation'] },
  { id: 'karim', initials: 'KI', name: 'Karim Idrissi', role: 'Analyste Risque', entity: 'Pôle Risques', skills: ['Scoring', 'IFRS 9', 'Modélisation'] },
  { id: 'nadia-e', initials: 'NE', name: 'Nadia El Amrani', role: 'Chargée de Clientèle Pro', entity: 'Banque de Détail', skills: ['Relation client', 'Négociation', 'Analyse financière'] },
  { id: 'youssef', initials: 'YA', name: 'Youssef Amrani', role: 'Contrôleur de Gestion', entity: 'Finance', skills: ['Reporting', 'Excel / SQL', 'Budget'] },
  { id: 'sofia', initials: 'SH', name: 'Sofia Haddad', role: 'Analyste Middle Office', entity: 'Corporate Banking', skills: ['Middle office', 'Conformité', 'Rigueur'] },
  { id: 'mehdi', initials: 'MC', name: 'Mehdi Chraibi', role: 'Trésorier Adjoint', entity: 'Finance & ALM', skills: ['ALM', 'Marchés', 'Liquidité'] },
  { id: 'sarah', initials: 'SK', name: 'Sarah Kabbaj', role: 'Directrice de Pôle', entity: 'Direction des Risques', skills: ['Leadership', 'Stratégie', 'Audit'] },
  { id: 'leila', initials: 'LT', name: 'Leïla Tazi', role: 'Data Analyst', entity: 'IT & Digital', skills: ['Python', 'Data viz', 'SQL'] },
  { id: 'omar', initials: 'OM', name: 'Omar Mansouri', role: 'Chef de Projet Digital', entity: 'IT & Digital', skills: ['Gestion de projet', 'Agile', 'Culture produit'] },
]
