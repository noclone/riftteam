const API_BASE = '/api'

/** Send a JSON request to the backend API and return the parsed response. */
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

/** HTTP error returned by the backend, carrying the status code. */
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
  }
}

/** API client with methods mapping to every backend endpoint. */
export const api = {
  /** Verify that a Riot ID exists and retrieve basic account info. */
  checkRiotId(name: string, tag: string) {
    return request<RiotCheckResponse>(`/riot/check/${encodeURIComponent(name)}/${encodeURIComponent(tag)}`)
  },
  /** Create a new player profile using a one-time action token. */
  createPlayer(data: PlayerCreateRequest, token: string) {
    return request<PlayerResponse>(`/players?token=${encodeURIComponent(token)}`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },
  /** Fetch a single player profile by slug, optionally with an edit token. */
  getPlayer(slug: string, token?: string) {
    const qs = token ? `?token=${encodeURIComponent(token)}` : ''
    return request<PlayerResponse>(`/players/${encodeURIComponent(slug)}${qs}`)
  },
  /** List players with optional query filters (is_lft, role, rank range, pagination). */
  listPlayers(params?: Record<string, string>) {
    const qs = params ? '?' + new URLSearchParams(params).toString() : ''
    return request<PlayerListResponse>(`/players${qs}`)
  },
  /** Update declarative fields on a player profile (requires edit token). */
  updatePlayer(slug: string, data: PlayerUpdateRequest, token: string) {
    return request<PlayerResponse>(`/players/${encodeURIComponent(slug)}?token=${encodeURIComponent(token)}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  },
  /** Delete a player profile permanently (requires edit token). */
  deletePlayer(slug: string, token: string) {
    return request<void>(`/players/${encodeURIComponent(slug)}?token=${encodeURIComponent(token)}`, {
      method: 'DELETE',
    })
  },
  /** Build the URL for downloading a player's data export (GDPR). */
  exportPlayer(slug: string, token: string) {
    return `${API_BASE}/players/${encodeURIComponent(slug)}/export?token=${encodeURIComponent(token)}`
  },
  /** Trigger a Riot data refresh for a player (subject to cooldown). */
  refreshPlayer(slug: string) {
    return request<PlayerResponse>(`/players/${encodeURIComponent(slug)}/refresh`, { method: 'POST' })
  },
  /** Validate an action token and return its metadata. */
  validateToken(token: string) {
    return request<TokenInfo>(`/tokens/${encodeURIComponent(token)}/validate`)
  },
  /** Create a new team using a one-time action token. */
  createTeam(data: TeamCreateRequest, token: string) {
    return request<TeamResponse>(`/teams?token=${encodeURIComponent(token)}`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },
  /** Fetch a single team by slug, optionally with an edit token. */
  getTeam(slug: string, token?: string) {
    const qs = token ? `?token=${encodeURIComponent(token)}` : ''
    return request<TeamResponse>(`/teams/${encodeURIComponent(slug)}${qs}`)
  },
  /** Update team fields (requires edit token). */
  updateTeam(slug: string, data: TeamUpdateRequest, token: string) {
    return request<TeamResponse>(`/teams/${encodeURIComponent(slug)}?token=${encodeURIComponent(token)}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  },
  /** Build the URL for downloading a team's data export (GDPR). */
  exportTeam(slug: string, token: string) {
    return `${API_BASE}/teams/${encodeURIComponent(slug)}/export?token=${encodeURIComponent(token)}`
  },
  /** Delete a team permanently (requires edit token). */
  deleteTeam(slug: string, token: string) {
    return request<void>(`/teams/${encodeURIComponent(slug)}?token=${encodeURIComponent(token)}`, {
      method: 'DELETE',
    })
  },
  /** List teams with optional query filters (is_lfp, role, rank range, pagination). */
  listTeams(params?: Record<string, string>) {
    const qs = params ? '?' + new URLSearchParams(params).toString() : ''
    return request<TeamListResponse>(`/teams${qs}`)
  },
  /** Check whether a team name is available. */
  checkTeamName(name: string, excludeSlug?: string) {
    const qs = excludeSlug ? `?exclude_slug=${encodeURIComponent(excludeSlug)}` : ''
    return request<{ available: boolean }>(`/teams/check-name/${encodeURIComponent(name)}${qs}`)
  },
}

/** Metadata returned when validating an action token. */
export interface TokenInfo {
  action: string
  discord_username: string
  game_name: string | null
  tag_line: string | null
  slug: string | null
  team_name: string | null
}

/** Account info returned by the Riot ID check endpoint. */
export interface RiotCheckResponse {
  game_name: string
  tag_line: string
  puuid: string
  summoner_level: number | null
  profile_icon_id: number | null
}

/** Champion mastery and ranked stats for a single champion. */
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

/** Full player profile including Riot data, declarative fields, and champions. */
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
  rank_flex_lp: number | null
  rank_flex_wins: number | null
  rank_flex_losses: number | null
  primary_role: string | null
  secondary_role: string | null
  summoner_level: number | null
  profile_icon_id: number | null
  discord_user_id: string | null
  discord_username: string | null
  description: string | null
  activities: string[] | null
  ambiance: string | null
  frequency_min: number | null
  frequency_max: number | null
  is_lft: boolean
  last_riot_sync: string | null
  created_at: string
  updated_at: string
  champions: ChampionResponse[]
}

/** Paginated list of player profiles. */
export interface PlayerListResponse {
  players: PlayerResponse[]
  total: number
}

/** Declarative fields sent when creating a player profile. */
export interface PlayerCreateRequest {
  description?: string
  activities?: string[]
  ambiance?: string
  frequency_min?: number
  frequency_max?: number
  is_lft?: boolean
}

/** Declarative fields that can be updated on an existing player profile. */
export interface PlayerUpdateRequest {
  description?: string
  activities?: string[]
  ambiance?: string
  frequency_min?: number
  frequency_max?: number
  is_lft?: boolean
}

/** A team roster member with their player summary and assigned role. */
export interface TeamMemberResponse {
  player: {
    id: string
    slug: string
    riot_game_name: string
    riot_tag_line: string
    rank_solo_tier: string | null
    rank_solo_division: string | null
    rank_solo_lp: number | null
    primary_role: string | null
    profile_icon_id: number | null
  }
  role: string
}

/** Full team profile including metadata, recruitment settings, and roster. */
export interface TeamResponse {
  id: string
  name: string
  slug: string
  captain_discord_id: string
  captain_discord_name: string | null
  description: string | null
  activities: string[] | null
  ambiance: string | null
  frequency_min: number | null
  frequency_max: number | null
  wanted_roles: string[] | null
  min_rank: string | null
  max_rank: string | null
  is_lfp: boolean
  created_at: string
  updated_at: string
  members: TeamMemberResponse[]
}

/** Paginated list of teams. */
export interface TeamListResponse {
  teams: TeamResponse[]
  total: number
}

/** Fields sent when creating a new team. */
export interface TeamCreateRequest {
  description?: string
  activities?: string[]
  ambiance?: string
  frequency_min?: number
  frequency_max?: number
  wanted_roles?: string[]
  min_rank?: string
  max_rank?: string
  is_lfp?: boolean
}

/** Fields that can be updated on an existing team. */
export interface TeamUpdateRequest {
  name?: string
  description?: string
  activities?: string[]
  ambiance?: string
  frequency_min?: number
  frequency_max?: number
  wanted_roles?: string[]
  min_rank?: string
  max_rank?: string
  is_lfp?: boolean
}
