import { ref } from 'vue'
import { RANK_COLORS } from '@/constants'

export const ddragonVersion = ref('15.3.1')

export async function fetchDDragonVersion() {
  try {
    const res = await fetch('https://ddragon.leagueoflegends.com/api/versions.json')
    const versions = await res.json()
    ddragonVersion.value = versions[0]
  } catch {
    // keep default
  }
}

export function profileIconUrl(iconId: number | null | undefined): string {
  if (!iconId) return ''
  return `https://ddragon.leagueoflegends.com/cdn/${ddragonVersion.value}/img/profileicon/${iconId}.png`
}

export function champIconUrl(name: string): string {
  const safe = name.replace(/ /g, '').replace(/'/g, '')
  return `https://ddragon.leagueoflegends.com/cdn/${ddragonVersion.value}/img/champion/${safe}.png`
}

export function rankIconUrl(tier: string): string {
  return `https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-static-assets/global/default/images/ranked-mini-crests/${tier.toLowerCase()}.png`
}

export function rankColor(tier: string | null): string {
  return RANK_COLORS[(tier || '').toUpperCase()] ?? '#6B6B6B'
}

export function formatRank(tier: string | null, division: string | null): string {
  if (!tier) return 'Unranked'
  const t = tier.charAt(0) + tier.slice(1).toLowerCase()
  if (['MASTER', 'GRANDMASTER', 'CHALLENGER'].includes(tier.toUpperCase())) return t
  return `${t} ${division ?? ''}`
}

export function formatTier(tier: string | null): string {
  if (!tier) return ''
  return tier.charAt(0) + tier.slice(1).toLowerCase()
}
