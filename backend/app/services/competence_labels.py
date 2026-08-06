"""Naturalisation des libellés de compétences.

Les libellés ESCO canoniques sont formulés en « action » (« Analyser des prêts »,
« Effectuer une analyse de risque », « Donner des conseils en investissement ») et
sonnent faux sur un CV, où l'on attend un intitulé de COMPÉTENCE (« Analyse de crédit »,
« Analyse des risques », « Conseil en investissement »).

`naturaliser()` reformule ces libellés en intitulés naturels, SANS toucher au
`skill_id` : l'ancrage ESCO (donc le matching reco/candidatures) reste identique.
Le mapping est volontairement conservateur (uniquement des libellés verbaux repérés).
"""

# Clés = libellé ESCO en minuscules, apostrophes droites (cf. naturaliser()).
_NATUREL: dict[str, str] = {
    "analyser des prêts": "Analyse de crédit",
    "analyser des systèmes d'information": "Analyse des systèmes d'information",
    "appliquer la gestion des risques à la passation de marchés": "Gestion des risques achats",
    "apporter une aide en cas de contentieux": "Gestion du contentieux",
    "assumer des responsabilités": "Sens des responsabilités",
    "assurer le respect de politiques": "Conformité aux politiques internes",
    "communiquer avec des professionnels du secteur bancaire": "Relations interbancaires",
    "communiquer des messages aux gens": "Communication",
    "communiquer par téléphone": "Relation client à distance",
    "concevoir une interface utilisateur": "Conception d'interfaces utilisateur",
    "coordonner des partenariats de tourisme public-privé": "Gestion de partenariats",
    "coordonner la sécurité": "Coordination de la sécurité",
    "donner des conseils en finance": "Conseil financier",
    "donner des conseils en investissement": "Conseil en investissement",
    "donner des conseils juridiques": "Conseil juridique",
    "développer des compétences personnelles": "Développement des compétences",
    "effectuer des opérations financières": "Opérations financières",
    "effectuer l'analyse d'une entreprise": "Analyse financière d'entreprise",
    "effectuer la gestion des risques liés à des opérations ferroviaires": "Gestion des risques opérationnels",
    "effectuer une analyse de risque": "Analyse des risques",
    "faire preuve d'une attitude professionnelle vis-à-vis de clients": "Sens du service client",
    "gérer des contrats": "Gestion contractuelle",
    "gérer des incidents": "Gestion des incidents",
    "gérer des processus": "Gestion des processus",
    "gérer des titres": "Gestion de titres",
    "gérer la progression personnelle": "Développement personnel",
    "gérer les comptes bancaires d'une entreprise": "Gestion des comptes entreprises",
    "gérer les données": "Gestion des données",
    "gérer les opérations de caisse": "Opérations de caisse",
    "gérer les ressources humaines": "Gestion des ressources humaines",
    "gérer un portfolio": "Gestion de portefeuille",
    "gérer un projet tic": "Gestion de projet IT",
    "gérer un service clients": "Gestion de la relation client",
    "gérer une base de données": "Gestion de bases de données",
    "négocier avec des parties prenantes": "Négociation",
    "organiser des formations": "Ingénierie de formation",
    "organiser un audit": "Conduite d'audit",
    "prendre contact avec des acheteurs": "Prospection commerciale",
    "prendre des décisions sur des demandes de prêt": "Décision d'octroi de crédit",
    "réaliser des audits informatiques": "Audit informatique",
    "soutenir des auteurs": "Accompagnement d'équipe",
    "superviser des activités bancaires": "Supervision des activités bancaires",
    "traiter des paiements": "Traitement des paiements",
    "travailler au sein des communautés": "Travail collaboratif",
    "élaborer des programmes de mobilité": "Gestion de la mobilité interne",
}


def naturaliser(libelle: str | None) -> str | None:
    """Renvoie la formulation naturelle d'un libellé ESCO verbal, ou le libellé
    inchangé s'il n'est pas dans le mapping. Insensible à la casse et au type
    d'apostrophe (droite ' ou courbe ’)."""
    if not libelle:
        return libelle
    key = libelle.strip().lower().replace("’", "'")
    return _NATUREL.get(key, libelle)
