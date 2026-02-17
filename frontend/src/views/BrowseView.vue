<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api, type PlayerResponse } from '@/api/client'

const players = ref<PlayerResponse[]>([])
const loading = ref(true)
const roleFilter = ref('')
const minRank = ref('')
const total = ref(0)
const offset = ref(0)
const PAGE_SIZE = 20

const DDRAGON_VERSION = ref('15.3.1')

const ROLE_LABELS: Record<string, string> = {
  TOP: 'Top',
  JUNGLE: 'Jungle',
  MIDDLE: 'Mid',
  BOTTOM: 'ADC',
  UTILITY: 'Support',
}

const RANK_TIERS = [
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

function profileIconUrl(p: PlayerResponse): string {
  if (!p.profile_icon_id) return ''
  return `https://ddragon.leagueoflegends.com/cdn/${DDRAGON_VERSION.value}/img/profileicon/${p.profile_icon_id}.png`
}

function champIconUrl(name: string): string {
  const safe = name.replace(/ /g, '').replace(/'/g, '')
  return `https://ddragon.leagueoflegends.com/cdn/${DDRAGON_VERSION.value}/img/champion/${safe}.png`
}

function rankColorFor(tier: string | null): string {
  return RANK_COLORS[(tier || '').toUpperCase()] ?? '#6B6B6B'
}

async function load() {
  loading.value = true
  const params: Record<string, string> = { is_lft: 'true', limit: String(PAGE_SIZE), offset: String(offset.value) }
  if (roleFilter.value) params.role = roleFilter.value
  if (minRank.value) params.min_rank = minRank.value
  const res = await api.listPlayers(params)
  players.value = res.players
  total.value = res.total
  loading.value = false
}

function setRole(role: string) {
  roleFilter.value = role
  offset.value = 0
  load()
}

function setMinRank() {
  offset.value = 0
  load()
}

function prevPage() {
  if (offset.value <= 0) return
  offset.value = Math.max(0, offset.value - PAGE_SIZE)
  load()
}

function nextPage() {
  if (offset.value + PAGE_SIZE >= total.value) return
  offset.value += PAGE_SIZE
  load()
}

function formatRank(p: PlayerResponse): string {
  if (!p.rank_solo_tier) return 'Unranked'
  const tier = p.rank_solo_tier.charAt(0) + p.rank_solo_tier.slice(1).toLowerCase()
  const apex = ['MASTER', 'GRANDMASTER', 'CHALLENGER']
  if (apex.includes(p.rank_solo_tier.toUpperCase())) return tier
  return `${tier} ${p.rank_solo_division ?? ''}`
}

function winRate(p: PlayerResponse): string {
  const w = p.rank_solo_wins ?? 0
  const l = p.rank_solo_losses ?? 0
  if (w + l === 0) return ''
  return `${Math.round((w / (w + l)) * 100)}%`
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

onMounted(async () => {
  await fetchDDragonVersion()
  await load()
})
</script>

<template>
  <div class="min-h-screen bg-gray-900 text-white p-4 sm:p-8">
    <div class="max-w-4xl mx-auto">
      <h1 class="text-3xl font-bold mb-6">Joueurs LFT</h1>

      <!-- Filters -->
      <div class="flex flex-wrap items-center gap-3 mb-6">
        <div class="flex flex-wrap gap-2">
          <button
            v-for="(label, key) in { '': 'Tous', ...ROLE_LABELS }"
            :key="key"
            :class="[
              'px-3 py-1.5 rounded-lg transition text-sm font-medium',
              roleFilter === key
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700',
            ]"
            @click="setRole(key as string)"
          >
            {{ label }}
          </button>
        </div>
        <select
          v-model="minRank"
          @change="setMinRank"
          class="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-300"
        >
          <option v-for="t in RANK_TIERS" :key="t.value" :value="t.value">{{ t.label }}</option>
        </select>
      </div>

      <div v-if="loading" class="text-center text-gray-400 mt-8">Chargement...</div>
      <div v-else-if="players.length === 0" class="text-center text-gray-500 mt-8">
        Aucun joueur trouvé.
      </div>
      <template v-else>
        <div class="space-y-3">
          <RouterLink
            v-for="p in players"
            :key="p.id"
            :to="`/p/${p.slug}`"
            class="block bg-gray-800 rounded-lg p-4 hover:bg-gray-750 transition"
          >
            <div class="flex items-center gap-4">
              <img
                v-if="profileIconUrl(p)"
                :src="profileIconUrl(p)"
                :alt="p.riot_game_name"
                class="w-12 h-12 rounded-lg flex-shrink-0"
              />
              <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2 min-w-0">
                    <span class="font-semibold truncate">{{ p.riot_game_name }}<span class="text-gray-500">#{{ p.riot_tag_line }}</span></span>
                    <span v-if="p.primary_role" class="text-gray-400 text-sm hidden sm:inline">
                      {{ ROLE_LABELS[p.primary_role] ?? p.primary_role }}
                    </span>
                  </div>
                  <div class="flex items-center gap-2 flex-shrink-0 ml-2">
                    <span class="text-sm font-semibold" :style="{ color: rankColorFor(p.rank_solo_tier) }">
                      {{ formatRank(p) }}
                    </span>
                    <span v-if="winRate(p)" class="text-xs text-gray-500">{{ winRate(p) }}</span>
                  </div>
                </div>
                <div v-if="p.champions.length" class="flex items-center gap-1 mt-1.5">
                  <img
                    v-for="champ in p.champions.slice(0, 3)"
                    :key="champ.champion_id"
                    :src="champIconUrl(champ.champion_name)"
                    :alt="champ.champion_name"
                    :title="champ.champion_name"
                    class="w-6 h-6 rounded"
                  />
                </div>
              </div>
            </div>
          </RouterLink>
        </div>

        <!-- Pagination -->
        <div class="flex items-center justify-between mt-6">
          <button
            :disabled="offset <= 0"
            @click="prevPage"
            class="px-4 py-2 text-sm bg-gray-800 hover:bg-gray-700 disabled:opacity-30 disabled:cursor-default rounded-lg transition"
          >
            Précédent
          </button>
          <span class="text-sm text-gray-500">
            {{ offset + 1 }}-{{ Math.min(offset + PAGE_SIZE, total) }} sur {{ total }}
          </span>
          <button
            :disabled="offset + PAGE_SIZE >= total"
            @click="nextPage"
            class="px-4 py-2 text-sm bg-gray-800 hover:bg-gray-700 disabled:opacity-30 disabled:cursor-default rounded-lg transition"
          >
            Suivant
          </button>
        </div>
      </template>
    </div>
  </div>
</template>
