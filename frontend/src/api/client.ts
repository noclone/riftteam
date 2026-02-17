const API_BASE = '/api'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new ApiError(res.status, body.detail ?? res.statusText)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
  }
}

export const api = {
  checkRiotId(name: string, tag: string) {
    return request<RiotCheckResponse>(`/riot/check/${encodeURIComponent(name)}/${encodeURIComponent(tag)}`)
  },
  createPlayer(data: PlayerCreateRequest) {
    return request<PlayerResponse>('/players', { method: 'POST', body: JSON.stringify(data) })
  },
  getPlayer(slug: string) {
    return request<PlayerResponse>(`/players/${encodeURIComponent(slug)}`)
  },
  listPlayers(params?: Record<string, string>) {
    const qs = params ? '?' + new URLSearchParams(params).toString() : ''
    return request<PlayerListResponse>(`/players${qs}`)
  },
  updatePlayer(slug: string, data: PlayerUpdateRequest) {
    return request<PlayerResponse>(`/players/${encodeURIComponent(slug)}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  },
  deletePlayer(slug: string) {
    return request<void>(`/players/${encodeURIComponent(slug)}`, { method: 'DELETE' })
  },
  refreshPlayer(slug: string) {
    return request<PlayerResponse>(`/players/${encodeURIComponent(slug)}/refresh`, { method: 'POST' })
  },
}

export interface RiotCheckResponse {
  game_name: string
  tag_line: string
  puuid: string
  summoner_level: number | null
  profile_icon_id: number | null
}

export interface ChampionResponse {
  champion_id: number
  champion_name: string
  mastery_level: number | null
  mastery_points: number | null
  games_played: number
  wins: number
  losses: number
  avg_kills: number | null
  avg_deaths: number | null
  avg_assists: number | null
}

export interface PlayerResponse {
  id: string
  slug: string
  riot_puuid: string
  riot_game_name: string
  riot_tag_line: string
  region: string
  rank_solo_tier: string | null
  rank_solo_division: string | null
  rank_solo_lp: number | null
  rank_solo_wins: number | null
  rank_solo_losses: number | null
  rank_flex_tier: string | null
  rank_flex_division: string | null
  primary_role: string | null
  secondary_role: string | null
  summoner_level: number | null
  profile_icon_id: number | null
  discord_username: string | null
  description: string | null
  looking_for: string | null
  ambition: string | null
  languages: string[] | null
  availability: Record<string, string[]> | null
  is_lft: boolean
  last_riot_sync: string | null
  created_at: string
  updated_at: string
  champions: ChampionResponse[]
}

export interface PlayerListResponse {
  players: PlayerResponse[]
  total: number
}

export interface PlayerCreateRequest {
  game_name: string
  tag_line: string
  discord_username?: string
  description?: string
  looking_for?: string
  ambition?: string
  languages?: string[]
  availability?: Record<string, string[]>
  is_lft?: boolean
}

export interface PlayerUpdateRequest {
  discord_username?: string
  description?: string
  looking_for?: string
  ambition?: string
  languages?: string[]
  availability?: Record<string, string[]>
  is_lft?: boolean
}
