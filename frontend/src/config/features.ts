/**
 * Drapeaux de fonctionnalité (front). Doivent rester cohérents avec le backend.
 */

/**
 * Publication DIRECTE d'offres par les managers.
 * DÉSACTIVÉE par décision RH : le manager exprime un BESOIN de recrutement, la
 * HRBP valide et publie l'offre. Pour réactiver un jour : passer à `true` ICI et
 * mettre le flag backend `MANAGER_PEUT_PUBLIER=true`. Le code de publication est
 * conservé (rien n'est perdu).
 */
export const MANAGER_PEUT_PUBLIER = false
