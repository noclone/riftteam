<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api, type PlayerResponse, type ChampionResponse } from '@/api/client'

const route = useRoute()
const player = ref<PlayerResponse | null>(null)
const loading = ref(true)
const error = ref('')
const refreshing = ref(false)
const refreshError = ref('')


const DDRAGON_VERSION = ref('15.3.1')

const ROLE_LABELS: Record<string, string> = {
  TOP: 'Toplaner',
  JUNGLE: 'Jungler',
  MIDDLE: 'Midlaner',
  BOTTOM: 'ADC',
  UTILITY: 'Support',
}

const ROLE_ICON_BASE = 'https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-clash/global/default/assets/images/position-selector/positions'
const ROLE_ICONS: Record<string, string> = {
  TOP: `${ROLE_ICON_BASE}/icon-position-top.png`,
  JUNGLE: `${ROLE_ICON_BASE}/icon-position-jungle.png`,
  MIDDLE: `${ROLE_ICON_BASE}/icon-position-middle.png`,
  BOTTOM: `${ROLE_ICON_BASE}/icon-position-bottom.png`,
  UTILITY: `${ROLE_ICON_BASE}/icon-position-utility.png`,
}

const ACTIVITY_LABELS: Record<string, string> = {
  SCRIMS: 'Scrims',
  TOURNOIS: 'Tournois',
  LAN: 'LAN',
  FLEX: 'Flex',
  CLASH: 'Clash',
}

const AMBIANCE_LABELS: Record<string, string> = {
  FUN: 'For fun',
  TRYHARD: 'Tryhard',
}

const RANK_COLORS: Record<string, string> = {
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

const rankColor = computed(() => {
  const tier = player.value?.rank_solo_tier?.toUpperCase()
  return tier ? RANK_COLORS[tier] ?? '#6B6B6B' : '#6B6B6B'
})

const flexRankColor = computed(() => {
  const tier = player.value?.rank_flex_tier?.toUpperCase()
  return tier ? RANK_COLORS[tier] ?? '#6B6B6B' : '#6B6B6B'
})

function rankIconUrl(tier: string): string {
  return `https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-static-assets/global/default/images/ranked-mini-crests/${tier.toLowerCase()}.png`
}

function profileIconUrl(p: PlayerResponse): string {
  if (!p.profile_icon_id) return ''
  return `https://ddragon.leagueoflegends.com/cdn/${DDRAGON_VERSION.value}/img/profileicon/${p.profile_icon_id}.png`
}

function champIconUrl(name: string): string {
  const safe = name.replace(/ /g, '').replace(/'/g, '')
  return `https://ddragon.leagueoflegends.com/cdn/${DDRAGON_VERSION.value}/img/champion/${safe}.png`
}

function formatRank(p: PlayerResponse): string {
  if (!p.rank_solo_tier) return 'Unranked'
  const tier = p.rank_solo_tier.charAt(0) + p.rank_solo_tier.slice(1).toLowerCase()
  const apex = ['MASTER', 'GRANDMASTER', 'CHALLENGER']
  if (apex.includes(p.rank_solo_tier.toUpperCase())) return tier
  return `${tier} ${p.rank_solo_division ?? ''}`
}

function formatRankFlex(p: PlayerResponse): string {
  if (!p.rank_flex_tier) return 'Unranked'
  const tier = p.rank_flex_tier.charAt(0) + p.rank_flex_tier.slice(1).toLowerCase()
  const apex = ['MASTER', 'GRANDMASTER', 'CHALLENGER']
  if (apex.includes(p.rank_flex_tier.toUpperCase())) return tier
  return `${tier} ${p.rank_flex_division ?? ''}`
}

function winRate(p: PlayerResponse): string {
  const w = p.rank_solo_wins ?? 0
  const l = p.rank_solo_losses ?? 0
  if (w + l === 0) return '-'
  return `${Math.round((w / (w + l)) * 100)}% WR`
}

function lpText(p: PlayerResponse): string {
  if (p.rank_solo_lp == null) return ''
  return `${p.rank_solo_lp} LP`
}

function champWr(champ: ChampionResponse): number {
  if (champ.games_played === 0) return 0
  return Math.round((champ.wins / champ.games_played) * 100)
}

function champKda(champ: ChampionResponse): string {
  if (champ.avg_kills == null || champ.avg_deaths == null || champ.avg_assists == null) return ''
  return `${champ.avg_kills.toFixed(1)} / ${champ.avg_deaths.toFixed(1)} / ${champ.avg_assists.toFixed(1)}`
}

function winsLosses(p: PlayerResponse): string {
  const w = p.rank_solo_wins ?? 0
  const l = p.rank_solo_losses ?? 0
  if (w + l === 0) return ''
  return `${w}W ${l}L`
}

function flexWinRate(p: PlayerResponse): string {
  const w = p.rank_flex_wins ?? 0
  const l = p.rank_flex_losses ?? 0
  if (w + l === 0) return '-'
  return `${Math.round((w / (w + l)) * 100)}% WR`
}

function flexLpText(p: PlayerResponse): string {
  if (p.rank_flex_lp == null) return ''
  return `${p.rank_flex_lp} LP`
}

function flexWinsLosses(p: PlayerResponse): string {
  const w = p.rank_flex_wins ?? 0
  const l = p.rank_flex_losses ?? 0
  if (w + l === 0) return ''
  return `${w}W ${l}L`
}

async function fetchDDragonVersion() {
  try {
    const res = await fetch('https://ddragon.leagueoflegends.com/api/versions.json')
    const versions = await res.json()
    DDRAGON_VERSION.value = versions[0]
  } catch {
    // keep default
  }
}

async function refreshProfile() {
  if (!player.value || refreshing.value) return
  refreshing.value = true
  refreshError.value = ''
  try {
    player.value = await api.refreshPlayer(player.value.slug)
  } catch (e: any) {
    refreshError.value = e.status === 429 ? 'Cooldown actif — réessaie plus tard.' : e.message
  } finally {
    refreshing.value = false
  }
}


onMounted(async () => {
  await fetchDDragonVersion()
  try {
    player.value = await api.getPlayer(route.params.slug as string)
  } catch (e: any) {
    error.value = e.status === 404 ? 'Profil introuvable ou actuellement pas LFT.' : e.message
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="min-h-screen bg-gray-900 text-white p-4 sm:p-8">
    <div v-if="loading" class="text-center text-gray-400 mt-20">Chargement...</div>
    <div v-else-if="error" class="text-center text-red-400 mt-20">{{ error }}</div>
    <div v-else-if="player" class="max-w-2xl mx-auto">
      <div
        class="bg-gray-800 rounded-xl overflow-hidden"
        :style="{ borderTop: `4px solid ${rankColor}` }"
      >
        <!-- Header -->
        <div class="p-6 pb-2 sm:p-8 sm:pb-2">
          <div class="flex items-start gap-4 sm:gap-6">
            <img
              v-if="profileIconUrl(player)"
              :src="profileIconUrl(player)"
              :alt="player.riot_game_name"
              class="w-20 h-20 sm:w-24 sm:h-24 rounded-xl flex-shrink-0"
            />
            <div class="flex-1 min-w-0">
              <h1 class="text-2xl sm:text-3xl font-bold truncate">
                {{ player.riot_game_name }}<span class="text-gray-500">#{{ player.riot_tag_line }}</span>
              </h1>
              <p class="text-gray-400 text-sm mt-1">Niveau {{ player.summoner_level }}</p>
            </div>
          </div>

          <!-- Ranks -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-6">
            <div class="bg-gray-700/50 rounded-lg p-4">
              <p class="text-xs text-gray-400 uppercase tracking-wide mb-2">Solo/Duo</p>
              <div class="flex items-center gap-3">
                <img
                  v-if="player.rank_solo_tier"
                  :src="rankIconUrl(player.rank_solo_tier)"
                  :alt="player.rank_solo_tier"
                  class="w-10 h-10"
                />
                <span class="text-lg font-bold" :style="{ color: rankColor }">{{ formatRank(player) }}</span>
                <span v-if="lpText(player)" class="text-sm text-gray-400">{{ lpText(player) }}</span>
              </div>
              <div class="flex items-center gap-3 text-sm text-gray-400 mt-1">
                <span>{{ winRate(player) }}</span>
                <span v-if="winsLosses(player)">{{ winsLosses(player) }}</span>
              </div>
            </div>
            <div class="bg-gray-700/50 rounded-lg p-4">
              <p class="text-xs text-gray-400 uppercase tracking-wide mb-2">Flex</p>
              <div class="flex items-center gap-3">
                <img
                  v-if="player.rank_flex_tier"
                  :src="rankIconUrl(player.rank_flex_tier)"
                  :alt="player.rank_flex_tier"
                  class="w-10 h-10"
                />
                <span class="text-lg font-bold" :style="{ color: flexRankColor }">{{ formatRankFlex(player) }}</span>
                <span v-if="flexLpText(player)" class="text-sm text-gray-400">{{ flexLpText(player) }}</span>
              </div>
              <div class="flex items-center gap-3 text-sm text-gray-400 mt-1">
                <span>{{ flexWinRate(player) }}</span>
                <span v-if="flexWinsLosses(player)">{{ flexWinsLosses(player) }}</span>
              </div>
            </div>
          </div>

          <!-- Roles -->
          <div class="flex gap-3 mt-4">
            <div v-if="player.primary_role" class="bg-gray-700/50 rounded-lg px-4 py-2 flex items-center gap-2">
              <img :src="ROLE_ICONS[player.primary_role]" :alt="player.primary_role" class="w-5 h-5" />
              <span class="font-semibold">{{ ROLE_LABELS[player.primary_role] ?? player.primary_role }}</span>
            </div>
            <div v-if="player.secondary_role" class="bg-gray-700/50 rounded-lg px-4 py-2 flex items-center gap-2">
              <img :src="ROLE_ICONS[player.secondary_role]" :alt="player.secondary_role" class="w-5 h-5" />
              <span class="font-semibold text-gray-400">{{ ROLE_LABELS[player.secondary_role] ?? player.secondary_role }}</span>
            </div>
          </div>

          <!-- External links -->
          <div class="flex flex-wrap gap-2 mt-4 mb-2">
            <a
              :href="`https://op.gg/lol/summoners/euw/${player.slug}`"
              target="_blank"
              rel="noopener"
              class="inline-flex items-center gap-1.5 bg-indigo-500/15 text-indigo-300 hover:bg-indigo-500/25 hover:text-indigo-200 text-sm px-3 py-1.5 rounded-lg transition"
            >
              <svg class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor"><path d="M4.25 5.5a.75.75 0 0 0-.75.75v8.5c0 .414.336.75.75.75h8.5a.75.75 0 0 0 .75-.75v-4a.75.75 0 0 1 1.5 0v4A2.25 2.25 0 0 1 12.75 17h-8.5A2.25 2.25 0 0 1 2 14.75v-8.5A2.25 2.25 0 0 1 4.25 4h5a.75.75 0 0 1 0 1.5h-5Z" /><path d="M6.194 12.753a.75.75 0 0 0 1.06.053L16.5 4.44v2.81a.75.75 0 0 0 1.5 0v-4.5a.75.75 0 0 0-.75-.75h-4.5a.75.75 0 0 0 0 1.5h2.553l-9.056 8.194a.75.75 0 0 0-.053 1.06Z" /></svg>
              OP.GG
            </a>
            <a
              :href="`https://www.deeplol.gg/summoner/EUW/${player.slug}`"
              target="_blank"
              rel="noopener"
              class="inline-flex items-center gap-1.5 bg-indigo-500/15 text-indigo-300 hover:bg-indigo-500/25 hover:text-indigo-200 text-sm px-3 py-1.5 rounded-lg transition"
            >
              <svg class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor"><path d="M4.25 5.5a.75.75 0 0 0-.75.75v8.5c0 .414.336.75.75.75h8.5a.75.75 0 0 0 .75-.75v-4a.75.75 0 0 1 1.5 0v4A2.25 2.25 0 0 1 12.75 17h-8.5A2.25 2.25 0 0 1 2 14.75v-8.5A2.25 2.25 0 0 1 4.25 4h5a.75.75 0 0 1 0 1.5h-5Z" /><path d="M6.194 12.753a.75.75 0 0 0 1.06.053L16.5 4.44v2.81a.75.75 0 0 0 1.5 0v-4.5a.75.75 0 0 0-.75-.75h-4.5a.75.75 0 0 0 0 1.5h2.553l-9.056 8.194a.75.75 0 0 0-.053 1.06Z" /></svg>
              DeepLoL
            </a>
            <a
              :href="`https://dpm.lol/${player.slug}`"
              target="_blank"
              rel="noopener"
              class="inline-flex items-center gap-1.5 bg-indigo-500/15 text-indigo-300 hover:bg-indigo-500/25 hover:text-indigo-200 text-sm px-3 py-1.5 rounded-lg transition"
            >
              <svg class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor"><path d="M4.25 5.5a.75.75 0 0 0-.75.75v8.5c0 .414.336.75.75.75h8.5a.75.75 0 0 0 .75-.75v-4a.75.75 0 0 1 1.5 0v4A2.25 2.25 0 0 1 12.75 17h-8.5A2.25 2.25 0 0 1 2 14.75v-8.5A2.25 2.25 0 0 1 4.25 4h5a.75.75 0 0 1 0 1.5h-5Z" /><path d="M6.194 12.753a.75.75 0 0 0 1.06.053L16.5 4.44v2.81a.75.75 0 0 0 1.5 0v-4.5a.75.75 0 0 0-.75-.75h-4.5a.75.75 0 0 0 0 1.5h2.553l-9.056 8.194a.75.75 0 0 0-.053 1.06Z" /></svg>
              DPM
            </a>
            <a
              :href="`https://www.leagueofgraphs.com/summoner/euw/${player.slug}#championsData-all-queues`"
              target="_blank"
              rel="noopener"
              class="inline-flex items-center gap-1.5 bg-indigo-500/15 text-indigo-300 hover:bg-indigo-500/25 hover:text-indigo-200 text-sm px-3 py-1.5 rounded-lg transition"
            >
              <svg class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor"><path d="M4.25 5.5a.75.75 0 0 0-.75.75v8.5c0 .414.336.75.75.75h8.5a.75.75 0 0 0 .75-.75v-4a.75.75 0 0 1 1.5 0v4A2.25 2.25 0 0 1 12.75 17h-8.5A2.25 2.25 0 0 1 2 14.75v-8.5A2.25 2.25 0 0 1 4.25 4h5a.75.75 0 0 1 0 1.5h-5Z" /><path d="M6.194 12.753a.75.75 0 0 0 1.06.053L16.5 4.44v2.81a.75.75 0 0 0 1.5 0v-4.5a.75.75 0 0 0-.75-.75h-4.5a.75.75 0 0 0 0 1.5h2.553l-9.056 8.194a.75.75 0 0 0-.053 1.06Z" /></svg>
              League of Graphs
            </a>
          </div>
        </div>

        <!-- LFT Info -->
        <div class="px-6 sm:px-8 pb-6 space-y-5">
          <div v-if="player.activities?.length || player.ambiance || (player.frequency_min != null && player.frequency_max != null)" class="flex flex-wrap gap-2.5">
            <span
              v-for="act in (player.activities ?? [])"
              :key="act"
              class="bg-cyan-600/20 text-cyan-300 text-base font-medium px-4 py-2 rounded-full"
            >
              {{ ACTIVITY_LABELS[act] ?? act }}
            </span>
            <span v-if="player.ambiance" :class="[
              'text-base font-medium px-4 py-2 rounded-full',
              player.ambiance === 'TRYHARD' ? 'bg-purple-600/20 text-purple-300' : 'bg-green-600/20 text-green-300',
            ]">
              {{ AMBIANCE_LABELS[player.ambiance] ?? player.ambiance }}
            </span>
            <span v-if="player.frequency_min != null && player.frequency_max != null" class="bg-gray-700/50 text-gray-300 text-base font-medium px-4 py-2 rounded-full">
              {{ player.frequency_min }}-{{ player.frequency_max }}x / semaine
            </span>
          </div>

          <div v-if="player.description" class="bg-gray-700/50 rounded-lg p-4">
            <p class="text-xs text-gray-400 uppercase tracking-wide mb-2">Description</p>
            <p class="text-gray-200 whitespace-pre-line leading-relaxed">{{ player.description }}</p>
          </div>
        </div>

        <!-- Champions -->
        <div v-if="player.champions.length" class="px-6 sm:px-8 pb-2">
          <h2 class="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Champions</h2>
          <div class="space-y-2">
            <div
              v-for="champ in player.champions.slice(0, 6)"
              :key="champ.champion_id"
              class="bg-gray-700/30 rounded-lg p-3 flex items-center gap-3"
            >
              <img
                :src="champIconUrl(champ.champion_name)"
                :alt="champ.champion_name"
                class="w-10 h-10 rounded"
              />
              <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between">
                  <span class="font-medium truncate">{{ champ.champion_name }}</span>
                  <span
                    :class="champWr(champ) >= 50 ? 'text-green-400' : 'text-red-400'"
                    class="font-semibold text-sm ml-2"
                  >
                    {{ champWr(champ) }}% WR
                  </span>
                </div>
                <div class="flex items-center gap-3 text-xs text-gray-400 mt-0.5">
                  <span>{{ champ.games_played }} games</span>
                  <span>{{ champ.wins }}W {{ champ.losses }}L</span>
                  <span v-if="champKda(champ)">{{ champKda(champ) }} KDA</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="pb-6"></div>
      </div>
    </div>
  </div>
</template>
