export const ROLE_LABELS: Record<string, string> = {
  TOP: 'Top',
  JUNGLE: 'Jungle',
  MIDDLE: 'Mid',
  BOTTOM: 'ADC',
  UTILITY: 'Support',
}

export const ROLE_LABELS_LONG: Record<string, string> = {
  TOP: 'Toplaner',
  JUNGLE: 'Jungler',
  MIDDLE: 'Midlaner',
  BOTTOM: 'ADC',
  UTILITY: 'Support',
}

const ROLE_ICON_BASE =
  'https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-clash/global/default/assets/images/position-selector/positions'

export const ROLE_ICONS: Record<string, string> = {
  TOP: `${ROLE_ICON_BASE}/icon-position-top.png`,
  JUNGLE: `${ROLE_ICON_BASE}/icon-position-jungle.png`,
  MIDDLE: `${ROLE_ICON_BASE}/icon-position-middle.png`,
  BOTTOM: `${ROLE_ICON_BASE}/icon-position-bottom.png`,
  UTILITY: `${ROLE_ICON_BASE}/icon-position-utility.png`,
}

export const ALL_ROLES = ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY'] as const

export const ACTIVITY_LABELS: Record<string, string> = {
  SCRIMS: 'Scrims',
  TOURNOIS: 'Tournois',
  LAN: 'LAN',
  FLEX: 'Flex',
  CLASH: 'Clash',
}

export const AMBIANCE_LABELS: Record<string, string> = {
  FUN: 'For fun',
  TRYHARD: 'Tryhard',
}

export const RANK_COLORS: Record<string, string> = {
  IRON: '#6B6B6B',
  BRONZE: '#8B4513',
  SILVER: '#C0C0C0',
  GOLD: '#FFD700',
  PLATINUM: '#00CED1',
  EMERALD: '#50C878',
  DIAMOND: '#4169E1',
  MASTER: '#9B30FF',
  GRANDMASTER: '#DC143C',
  CHALLENGER: '#F0E68C',
}

export const RANK_TIERS = [
  { value: '', label: 'Tous les rangs' },
  { value: 'IRON', label: 'Iron+' },
  { value: 'BRONZE', label: 'Bronze+' },
  { value: 'SILVER', label: 'Silver+' },
  { value: 'GOLD', label: 'Gold+' },
  { value: 'PLATINUM', label: 'Platinum+' },
  { value: 'EMERALD', label: 'Emerald+' },
  { value: 'DIAMOND', label: 'Diamond+' },
  { value: 'MASTER', label: 'Master+' },
]
