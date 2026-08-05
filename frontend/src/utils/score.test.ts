import { describe, it, expect } from 'vitest'
import { scoreTone, scoreText, scoreBar, scoreLabel, byPctDesc } from './score'

describe('scoreTone', () => {
  it('vert ≥ 70, orange 40–69, rouge < 40 (bornes incluses)', () => {
    expect(scoreTone(100)).toBe('green')
    expect(scoreTone(70)).toBe('green')
    expect(scoreTone(69)).toBe('warn')
    expect(scoreTone(40)).toBe('warn')
    expect(scoreTone(39)).toBe('danger')
    expect(scoreTone(0)).toBe('danger')
  })
  it('mappe classes et intitulés', () => {
    expect(scoreText(80)).toBe('text-green-deep')
    expect(scoreBar(50)).toBe('bg-warning')
    expect(scoreText(10)).toBe('text-danger')
    expect(scoreLabel(80)).toBe('Maîtrisé')
    expect(scoreLabel(50)).toBe('À consolider')
    expect(scoreLabel(10)).toBe('À développer')
  })
})

describe('byPctDesc', () => {
  it('trie strictement décroissant sans muter, départage stable', () => {
    const src = [
      { label: 'B', pct: 40 },
      { label: 'A', pct: 90 },
      { label: 'C', pct: 40 },
    ]
    const out = byPctDesc(src)
    expect(out.map((x) => x.label)).toEqual(['A', 'B', 'C']) // 90, puis 40 A<B<C
    expect(src[0].label).toBe('B') // source non mutée
  })
})
