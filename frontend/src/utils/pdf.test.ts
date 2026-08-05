import { describe, it, expect } from 'vitest'
import { buildPdf, type PdfBlock } from './pdf'

async function pdfText(blocks: PdfBlock[]): Promise<string> {
  const buf = await buildPdf(blocks).arrayBuffer()
  // Latin-1 : chaque octet → un caractère (le PDF est ASCII/WinAnsi).
  return Array.from(new Uint8Array(buf), (b) => String.fromCharCode(b)).join('')
}

describe('buildPdf', () => {
  it('produit un PDF valide (en-tête + trailer)', async () => {
    const s = await pdfText([{ type: 'h1', text: 'Titre' }, { type: 'p', text: 'Un paragraphe.' }])
    expect(s.startsWith('%PDF-1.4')).toBe(true)
    expect(s).toContain('/Type /Catalog')
    expect(s).toContain('startxref')
    expect(s.trimEnd().endsWith('%%EOF')).toBe(true)
  })

  it('échappe les parenthèses et gère les accents/typographie', async () => {
    const s = await pdfText([{ type: 'p', text: 'Réussite (chiffrée) — élan « clé »' }])
    expect(s).toContain('Réussite') // é en Latin-1 (0xE9)
    expect(s).toContain('\\(') // parenthèse ouvrante échappée
    expect(s).toContain('\\)')
    // em dash — mappé sur l'octet WinAnsi 0x97
    expect(s).toContain(String.fromCharCode(0x97))
  })

  it('pagine les contenus longs sur plusieurs pages', async () => {
    const blocks: PdfBlock[] = Array.from({ length: 120 }, (_, i) => ({ type: 'p', text: `Ligne ${i} de contenu à paginer.` }))
    const s = await pdfText(blocks)
    const count = (s.match(/\/Type \/Page[^s]/g) || []).length
    expect(count).toBeGreaterThan(1)
  })
})
