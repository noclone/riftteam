<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { api, type TeamResponse } from '@/api/client'

const route = useRoute()
const team = ref<TeamResponse | null>(null)
const loading = ref(true)
const error = ref('')

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

const ALL_ROLES = ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY']

function rankIconUrl(tier: string): string {
  return `https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-static-assets/global/default/images/ranked-mini-crests/${tier.toLowerCase()}.png`
}

function profileIconUrl(iconId: number | null): string {
  if (!iconId) return ''
  return `https://ddragon.leagueoflegends.com/cdn/${DDRAGON_VERSION.value}/img/profileicon/${iconId}.png`
}

function formatRank(tier: string | null, division: string | null): string {
  if (!tier) return 'Unranked'
  const t = tier.charAt(0) + tier.slice(1).toLowerCase()
  if (['MASTER', 'GRANDMASTER', 'CHALLENGER'].includes(tier.toUpperCase())) return t
  return `${t} ${division ?? ''}`
}

function rankColor(tier: string | null): string {
  return tier ? RANK_COLORS[tier.toUpperCase()] ?? '#6B6B6B' : '#6B6B6B'
}

const membersByRole = computed(() => {
  const map: Record<string, TeamResponse['members'][number]> = {}
  for (const m of team.value?.members ?? []) {
    map[m.role] = m
  }
  return map
})

async function fetchDDragonVersion() {
  try {
    const res = await fetch('https://ddragon.leagueoflegends.com/api/versions.json')
    const versions = await res.json()
    DDRAGON_VERSION.value = versions[0]
  } catch {
    // keep default
  }
}

onMounted(async () => {
  await fetchDDragonVersion()
  try {
    team.value = await api.getTeam(route.params.slug as string)
  } catch (e: any) {
    error.value = e.status === 404 ? 'Équipe introuvable.' : e.message
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="bg-gray-900 text-white p-4 sm:p-8">
    <div v-if="loading" class="text-center text-gray-400 mt-20">Chargement...</div>
    <div v-else-if="error" class="text-center text-red-400 mt-20">{{ error }}</div>
    <div v-else-if="team" class="max-w-2xl mx-auto">
      <div class="bg-gray-800 rounded-xl overflow-hidden border-t-4 border-indigo-500">
        <!-- Header -->
        <div class="p-6 sm:p-8">
          <h1 class="text-3xl font-bold mb-1">{{ team.name }}</h1>
          <p v-if="team.captain_discord_name" class="text-gray-400 text-sm">
            Capitaine : {{ team.captain_discord_name }}
          </p>

          <!-- Elo range -->
          <div v-if="team.min_rank || team.max_rank" class="mt-4 flex items-center gap-2">
            <template v-if="team.min_rank">
              <img :src="rankIconUrl(team.min_rank)" :alt="team.min_rank" class="w-7 h-7" />
              <span class="font-semibold" :style="{ color: RANK_COLORS[team.min_rank.toUpperCase()] ?? '#fff' }">
                {{ team.min_rank.charAt(0).toUpperCase() + team.min_rank.slice(1).toLowerCase() }}
              </span>
            </template>
            <span v-if="team.min_rank && team.max_rank" class="text-gray-500">→</span>
            <template v-if="team.max_rank">
              <img :src="rankIconUrl(team.max_rank)" :alt="team.max_rank" class="w-7 h-7" />
              <span class="font-semibold" :style="{ color: RANK_COLORS[team.max_rank.toUpperCase()] ?? '#fff' }">
                {{ team.max_rank.charAt(0).toUpperCase() + team.max_rank.slice(1).toLowerCase() }}
              </span>
            </template>
          </div>

          <!-- Chips -->
          <div v-if="team.activities?.length || team.ambiance || (team.frequency_min != null && team.frequency_max != null)" class="flex flex-wrap gap-2.5 mt-4">
            <span
              v-for="act in (team.activities ?? [])"
              :key="act"
              class="bg-cyan-600/20 text-cyan-300 text-base font-medium px-4 py-2 rounded-full"
            >
              {{ ACTIVITY_LABELS[act] ?? act }}
            </span>
            <span v-if="team.ambiance" :class="[
              'text-base font-medium px-4 py-2 rounded-full',
              team.ambiance === 'TRYHARD' ? 'bg-purple-600/20 text-purple-300' : 'bg-green-600/20 text-green-300',
            ]">
              {{ AMBIANCE_LABELS[team.ambiance] ?? team.ambiance }}
            </span>
            <span v-if="team.frequency_min != null && team.frequency_max != null" class="bg-gray-700/50 text-gray-300 text-base font-medium px-4 py-2 rounded-full">
              {{ team.frequency_min }}-{{ team.frequency_max }}x / semaine
            </span>
          </div>

          <!-- Description -->
          <div v-if="team.description" class="bg-gray-700/50 rounded-lg p-4 mt-4">
            <p class="text-xs text-gray-400 uppercase tracking-wide mb-2">Description</p>
            <p class="text-gray-200 whitespace-pre-line leading-relaxed">{{ team.description }}</p>
          </div>
        </div>

        <!-- Roster -->
        <div class="px-6 sm:px-8 pb-6">
          <h2 class="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Roster</h2>
          <div class="space-y-2">
            <template v-for="role in ALL_ROLES" :key="role">
              <div
                v-if="membersByRole[role]"
                class="bg-gray-700/30 rounded-lg p-3 flex items-center gap-3"
              >
                <img :src="ROLE_ICONS[role]" :alt="role" class="w-6 h-6 opacity-70" />
                <img
                  v-if="profileIconUrl(membersByRole[role].player.profile_icon_id)"
                  :src="profileIconUrl(membersByRole[role].player.profile_icon_id)"
                  class="w-10 h-10 rounded"
                />
                <div class="flex-1 min-w-0">
                  <RouterLink
                    :to="`/p/${membersByRole[role].player.slug}`"
                    class="font-medium hover:text-indigo-300 transition"
                  >
                    {{ membersByRole[role].player.riot_game_name }}<span class="text-gray-500">#{{ membersByRole[role].player.riot_tag_line }}</span>
                  </RouterLink>
                  <div class="flex items-center gap-1.5 mt-0.5">
                    <img
                      v-if="membersByRole[role].player.rank_solo_tier"
                      :src="rankIconUrl(membersByRole[role].player.rank_solo_tier!)"
                      :alt="membersByRole[role].player.rank_solo_tier!"
                      class="w-5 h-5"
                    />
                    <span class="text-sm font-semibold" :style="{ color: rankColor(membersByRole[role].player.rank_solo_tier) }">
                      {{ formatRank(membersByRole[role].player.rank_solo_tier, membersByRole[role].player.rank_solo_division) }}
                    </span>
                    <span
                      v-if="membersByRole[role].player.rank_solo_lp != null && membersByRole[role].player.rank_solo_tier"
                      class="text-xs"
                      :style="{ color: rankColor(membersByRole[role].player.rank_solo_tier) }"
                    >
                      {{ membersByRole[role].player.rank_solo_lp }} LP
                    </span>
                  </div>
                </div>
                <span class="text-sm text-gray-400">{{ ROLE_LABELS[role] }}</span>
              </div>
              <div
                v-else-if="team.wanted_roles?.includes(role)"
                class="bg-gray-700/10 border border-dashed border-gray-600 rounded-lg p-3 flex items-center gap-3"
              >
                <img :src="ROLE_ICONS[role]" :alt="role" class="w-6 h-6 opacity-40" />
                <span class="text-gray-500 italic">{{ ROLE_LABELS[role] }} recherché</span>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
