/**
 * coachFormat.ts — Rend le markdown léger des réponses du Coach (LLM) en HTML sûr.
 *
 * SÉCURITÉ
 *   Le texte vient d'un modèle : on ÉCHAPPE d'abord tout le HTML, PUIS on
 *   ré-injecte uniquement un jeu restreint de balises connues (<strong>, <em>,
 *   <code>, <ul>/<li>, <br>). Aucune balise du LLM ne peut donc s'exécuter.
 *
 * PORTÉE
 *   Markdown volontairement minimal (ce que qwen3 produit en pratique) :
 *   **gras**, *italique*, `code`, listes à puces «- »/«* », sauts de ligne.
 *   Les listes numérotées restent en clair (déjà lisibles : « 1. … »).
 *   Rendu identique en streaming (fragment par fragment) et en un bloc : un
 *   `**` non encore fermé reste littéral jusqu'à l'arrivée de sa paire.
 *
 *   Listes : styles INLINE (le HTML injecté via v-html n'est pas balayé par
 *   Tailwind — une classe utilitaire ne s'y appliquerait pas de façon fiable).
 */

function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

export function formatCoachReply(raw: string): string {
  let html = escapeHtml(raw || '')

  // --- Inline : gras avant italique (le gras utilise une paire de *). ---
  html = html
    .replace(/\*\*([^\n*]+?)\*\*/g, '<strong>$1</strong>') // **gras**
    .replace(/`([^`\n]+?)`/g, '<code>$1</code>') // `code`
    // *italique* / _italique_ : bornés par un espace/ponctuation pour éviter
    // les faux positifs (ex. « 3 * 4 », noms_avec_underscores).
    .replace(/(^|[\s(])\*(?!\s)([^*\n]+?)\*(?=[\s).,;:!?]|$)/g, '$1<em>$2</em>')
    .replace(/(^|[\s(])_(?!\s)([^_\n]+?)_(?=[\s).,;:!?]|$)/g, '$1<em>$2</em>')

  // --- Listes à puces : lignes «- » ou «* » consécutives → <ul><li>. ---
  const lines = html.split('\n')
  const out: string[] = []
  let inList = false
  const closeList = (): void => {
    if (inList) {
      out.push('</ul>')
      inList = false
    }
  }
  for (const line of lines) {
    const m = line.match(/^\s*[-*]\s+(.+)$/)
    if (m) {
      if (!inList) {
        out.push('<ul style="list-style:disc;margin:.3rem 0;padding-left:1.15rem">')
        inList = true
      }
      out.push(`<li>${m[1]}</li>`)
    } else {
      closeList()
      out.push(line)
    }
  }
  closeList()
  html = out.join('\n')

  // --- Sauts de ligne restants → <br>, sans en coller autour des listes. ---
  return html
    .replace(/\n{2,}/g, '<br><br>')
    .replace(/\n/g, '<br>')
    .replace(/<br>\s*(<\/?(?:ul|li)[^>]*>)/g, '$1')
    .replace(/(<\/(?:ul|li)>)\s*<br>/g, '$1')
}
