/**
 * pdf.ts — Générateur PDF minimal, SANS dépendance externe (offline / CSP-safe).
 *
 * Produit un PDF texte multi-pages (Helvetica + Helvetica-Bold, encodage WinAnsi)
 * à partir de blocs structurés. Suffisant pour un livrable imprimable/archivable
 * comme la synthèse de préparation d'entretien. Pas de rendu riche (images, couleurs) :
 * volontairement simple et robuste, aucun paquet à installer.
 */

export type PdfBlock =
  | { type: 'h1' | 'h2' | 'p'; text: string }
  | { type: 'spacer' }

// A4 en points PostScript.
const PAGE_W = 595
const PAGE_H = 842
const MARGIN = 56
const TEXT_W = PAGE_W - 2 * MARGIN

interface Style { font: 'F1' | 'F2'; size: number; leading: number }
const STYLE: Record<'h1' | 'h2' | 'p', Style> = {
  h1: { font: 'F2', size: 17, leading: 24 },
  h2: { font: 'F2', size: 13, leading: 19 },
  p: { font: 'F1', size: 10.5, leading: 15 },
}

// Unicode → octet WinAnsi pour les caractères typographiques hors Latin-1 bas.
const WINANSI_EXTRA: Record<string, number> = {
  '€': 0x80, '‚': 0x82, 'ƒ': 0x83, '„': 0x84, '…': 0x85, '†': 0x86, '‡': 0x87,
  'ˆ': 0x88, '‰': 0x89, 'Š': 0x8a, '‹': 0x8b, 'Œ': 0x8c, 'Ž': 0x8e,
  '‘': 0x91, '’': 0x92, '“': 0x93, '”': 0x94, '•': 0x95, '–': 0x96, '—': 0x97,
  '˜': 0x98, '™': 0x99, 'š': 0x9a, '›': 0x9b, 'œ': 0x9c, 'ž': 0x9e, 'Ÿ': 0x9f,
}

/** Convertit une chaîne en littéral PDF (octets WinAnsi, échappement ( ) \ ). */
function pdfString(s: string): string {
  let out = ''
  for (const ch of s) {
    const code = ch.codePointAt(0) ?? 0x3f
    let byte: number
    if (WINANSI_EXTRA[ch] !== undefined) byte = WINANSI_EXTRA[ch]
    else if (code <= 0xff) byte = code
    else byte = 0x3f // hors jeu → '?'
    if (byte === 0x28 || byte === 0x29 || byte === 0x5c) out += '\\' // ( ) \
    out += String.fromCharCode(byte)
  }
  return out
}

/** Découpe un paragraphe en lignes tenant dans TEXT_W (largeur estimée ~0,5 em). */
function wrap(text: string, size: number): string[] {
  const maxChars = Math.max(8, Math.floor(TEXT_W / (size * 0.5)))
  const words = text.replace(/\s+/g, ' ').trim().split(' ')
  const lines: string[] = []
  let cur = ''
  for (const w of words) {
    if (!cur) { cur = w; continue }
    if ((cur + ' ' + w).length <= maxChars) cur += ' ' + w
    else { lines.push(cur); cur = w }
  }
  if (cur) lines.push(cur)
  return lines.length ? lines : ['']
}

interface Line { text: string; style: Style }

/** Aplati les blocs en lignes stylées (avec retour à la ligne). */
function layout(blocks: PdfBlock[]): Line[] {
  const lines: Line[] = []
  for (const b of blocks) {
    if (b.type === 'spacer') { lines.push({ text: '', style: STYLE.p }); continue }
    const st = STYLE[b.type]
    for (const l of wrap(b.text, st.size)) lines.push({ text: l, style: st })
  }
  return lines
}

/** Construit le flux de contenu d'une page à partir de ses lignes positionnées. */
function pageContent(lines: Line[]): string {
  let y = PAGE_H - MARGIN
  let out = ''
  for (const ln of lines) {
    y -= ln.style.leading
    if (ln.text) {
      out += `BT /${ln.style.font} ${ln.style.size} Tf ${MARGIN} ${y.toFixed(1)} Td (${pdfString(ln.text)}) Tj ET\n`
    }
  }
  return out
}

/** Répartit les lignes en pages (hauteur utile). */
function paginate(lines: Line[]): Line[][] {
  const usable = PAGE_H - 2 * MARGIN
  const pages: Line[][] = []
  let cur: Line[] = []
  let h = 0
  for (const ln of lines) {
    if (h + ln.style.leading > usable && cur.length) { pages.push(cur); cur = []; h = 0 }
    cur.push(ln)
    h += ln.style.leading
  }
  if (cur.length) pages.push(cur)
  return pages.length ? pages : [[]]
}

/** Génère un Blob PDF à partir des blocs. */
export function buildPdf(blocks: PdfBlock[]): Blob {
  const pages = paginate(layout(blocks))

  // Objets : 1 catalog, 2 pages, 3 font, 4 fontBold, puis (page + contenu) × N.
  const objects: string[] = []
  const pageObjNums: number[] = []
  const firstPageObj = 5
  pages.forEach((_, i) => pageObjNums.push(firstPageObj + i * 2))

  objects[1] = `<< /Type /Catalog /Pages 2 0 R >>`
  objects[2] = `<< /Type /Pages /Kids [${pageObjNums.map((n) => `${n} 0 R`).join(' ')}] /Count ${pages.length} >>`
  objects[3] = `<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>`
  objects[4] = `<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>`

  pages.forEach((lns, i) => {
    const pageNum = firstPageObj + i * 2
    const contentNum = pageNum + 1
    const content = pageContent(lns)
    objects[pageNum] =
      `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${PAGE_W} ${PAGE_H}] ` +
      `/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents ${contentNum} 0 R >>`
    objects[contentNum] = `<< /Length ${content.length} >>\nstream\n${content}endstream`
  })

  // Sérialisation + table xref.
  let pdf = '%PDF-1.4\n'
  const offsets: number[] = []
  const maxObj = objects.length - 1
  for (let n = 1; n <= maxObj; n++) {
    if (objects[n] === undefined) continue
    offsets[n] = pdf.length
    pdf += `${n} 0 obj\n${objects[n]}\nendobj\n`
  }
  const xrefPos = pdf.length
  pdf += `xref\n0 ${maxObj + 1}\n0000000000 65535 f \n`
  for (let n = 1; n <= maxObj; n++) {
    const off = offsets[n] ?? 0
    pdf += `${String(off).padStart(10, '0')} 00000 n \n`
  }
  pdf += `trailer\n<< /Size ${maxObj + 1} /Root 1 0 R >>\nstartxref\n${xrefPos}\n%%EOF`

  // Chaque char de `pdf` est déjà un octet (0-255) → Latin-1 vers bytes.
  const bytes = new Uint8Array(pdf.length)
  for (let i = 0; i < pdf.length; i++) bytes[i] = pdf.charCodeAt(i) & 0xff
  return new Blob([bytes], { type: 'application/pdf' })
}

/** Déclenche le téléchargement d'un PDF construit à partir de blocs. */
export function downloadPdf(filename: string, blocks: PdfBlock[]): void {
  const url = URL.createObjectURL(buildPdf(blocks))
  const a = document.createElement('a')
  a.href = url
  a.download = filename.endsWith('.pdf') ? filename : `${filename}.pdf`
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
