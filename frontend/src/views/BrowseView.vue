<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { api, type PlayerResponse, type TeamResponse } from '@/api/client'
import { ROLE_LABELS, ROLE_ICONS, ALL_ROLES, ACTIVITY_LABELS, AMBIANCE_LABELS, RANK_TIERS } from '@/constants'
import {
  fetchDDragonVersion,
  profileIconUrl,
  champIconUrl,
  rankIconUrl,
  rankColor,
  formatRank,
  formatTier,
} from '@/utils'

const route = useRoute()

const activeTab = ref<'players' | 'teams'>(route.query.tab === 'teams' ? 'teams' : 'players')
const players = ref<PlayerResponse[]>([])
const teams = ref<TeamResponse[]>([])
const loading = ref(true)
const roleFilter = ref('')
const minRank = ref('')
const total = ref(0)
const teamTotal = ref(0)
const offset = ref(0)
const PAGE_SIZE = 20

const currentTotal = computed(() => (activeTab.value === 'teams' ? teamTotal.value : total.value))

function teamMembersByRole(t: TeamResponse): Record<string, TeamResponse['members'][number]> {
  const map: Record<string, TeamResponse['members'][number]> = {}
  for (const m of t.members) map[m.role] = m
  return map
}

function formatPlayerRank(p: PlayerResponse): string {
  return formatRank(p.rank_solo_tier, p.rank_solo_division)
}

function winRate(p: PlayerResponse): string {
  const w = p.rank_solo_wins ?? 0
  const l = p.rank_solo_losses ?? 0
  if (w + l === 0) return ''
  return `${Math.round((w / (w + l)) * 100)}%`
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

async function loadTeams() {
  loading.value = true
  const params: Record<string, string> = { is_lfp: 'true', limit: String(PAGE_SIZE), offset: String(offset.value) }
  if (roleFilter.value) params.role = roleFilter.value
  if (minRank.value) params.min_rank = minRank.value
  const res = await api.listTeams(params)
  teams.value = res.teams
  teamTotal.value = res.total
  loading.value = false
}

function loadActive() {
  return activeTab.value === 'teams' ? loadTeams() : load()
}

function switchTab(tab: 'players' | 'teams') {
  if (activeTab.value === tab) return
  activeTab.value = tab
  offset.value = 0
  roleFilter.value = ''
  minRank.value = ''
  loadActive()
}

function setRole(role: string) {
  roleFilter.value = role
  offset.value = 0
  loadActive()
}

function setMinRank() {
  offset.value = 0
  loadActive()
}

function prevPage() {
  if (offset.value <= 0) return
  offset.value = Math.max(0, offset.value - PAGE_SIZE)
  loadActive()
}

function nextPage() {
  if (offset.value + PAGE_SIZE >= currentTotal.value) return
  offset.value += PAGE_SIZE
  loadActive()
}

onMounted(async () => {
  await fetchDDragonVersion()
  await loadActive()
})
</script>

<template>
  <div class="bg-gray-900 text-white p-4 sm:p-8">
    <div class="max-w-4xl mx-auto">
      <h1 class="text-3xl font-bold mb-6">Parcourir</h1>

      <!-- Tabs -->
      <div class="flex gap-2 mb-6">
        <button
          :class="[
            'px-4 py-2 rounded-lg transition text-sm font-medium',
            activeTab === 'players' ? 'bg-indigo-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700',
          ]"
          @click="switchTab('players')"
        >
          Joueurs
        </button>
        <button
          :class="[
            'px-4 py-2 rounded-lg transition text-sm font-medium',
            activeTab === 'teams' ? 'bg-indigo-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700',
          ]"
          @click="switchTab('teams')"
        >
          Équipes
        </button>
      </div>

      <!-- Filters -->
      <div class="flex flex-wrap items-center gap-3 mb-6">
        <div class="flex flex-wrap gap-2">
          <button
            v-for="(label, key) in { '': 'Tous', ...ROLE_LABELS }"
            :key="key"
            :class="[
              'px-3 py-1.5 rounded-lg transition text-sm font-medium',
              roleFilter === key ? 'bg-indigo-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700',
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

      <!-- Players list -->
      <template v-else-if="activeTab === 'players'">
        <div v-if="players.length === 0" class="text-center text-gray-500 mt-8">Aucun joueur trouvé.</div>
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
                  v-if="profileIconUrl(p.profile_icon_id)"
                  :src="profileIconUrl(p.profile_icon_id)"
                  :alt="p.riot_game_name"
                  class="w-12 h-12 rounded-lg flex-shrink-0"
                />
                <div class="flex-1 min-w-0">
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2 min-w-0">
                      <span class="font-semibold truncate"
                        >{{ p.riot_game_name }}<span class="text-gray-500">#{{ p.riot_tag_line }}</span></span
                      >
                      <span v-if="p.primary_role" class="text-gray-400 text-sm hidden sm:inline">
                        {{ ROLE_LABELS[p.primary_role] ?? p.primary_role }}
                      </span>
                    </div>
                    <div class="flex items-center gap-2 flex-shrink-0 ml-2">
                      <span class="text-sm font-semibold" :style="{ color: rankColor(p.rank_solo_tier) }">
                        {{ formatPlayerRank(p) }}
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
      </template>

      <!-- Teams list -->
      <template v-else-if="activeTab === 'teams'">
        <div v-if="teams.length === 0" class="text-center text-gray-500 mt-8">Aucune équipe trouvée.</div>
        <template v-else>
          <div class="space-y-3">
            <RouterLink
              v-for="t in teams"
              :key="t.id"
              :to="`/t/${t.slug}`"
              class="block bg-gray-800 rounded-lg p-4 hover:bg-gray-750 transition"
            >
              <div class="flex items-center gap-2 mb-3">
                <span class="font-semibold truncate">{{ t.name }}</span>
                <span class="text-xs text-gray-500">{{ t.members.length }}/5</span>
                <template v-if="t.min_rank || t.max_rank">
                  <span class="text-gray-700 mx-1">·</span>
                  <div class="flex items-center gap-1">
                    <template v-if="t.min_rank">
                      <img :src="rankIconUrl(t.min_rank)" :alt="t.min_rank" class="w-5 h-5" />
                      <span class="text-sm font-medium" :style="{ color: rankColor(t.min_rank) }">{{
                        formatTier(t.min_rank)
                      }}</span>
                    </template>
                    <svg
                      v-if="t.min_rank && t.max_rank"
                      class="w-4 h-4 text-gray-500"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    >
                      <path d="M5 12h14M13 6l6 6-6 6" />
                    </svg>
                    <template v-if="t.max_rank">
                      <img :src="rankIconUrl(t.max_rank)" :alt="t.max_rank" class="w-5 h-5" />
                      <span class="text-sm font-medium" :style="{ color: rankColor(t.max_rank) }">{{
                        formatTier(t.max_rank)
                      }}</span>
                    </template>
                  </div>
                </template>
              </div>
              <div class="flex gap-4">
                <div class="flex-1 min-w-0">
                  <div
                    v-if="t.activities?.length || t.ambiance || (t.frequency_min != null && t.frequency_max != null)"
                    class="flex flex-wrap gap-1.5 mb-3"
                  >
                    <span
                      v-for="act in t.activities ?? []"
                      :key="act"
                      class="bg-cyan-600/20 text-cyan-300 text-xs font-medium px-2 py-0.5 rounded-full"
                    >
                      {{ ACTIVITY_LABELS[act] ?? act }}
                    </span>
                    <span
                      v-if="t.ambiance"
                      :class="[
                        'text-xs font-medium px-2 py-0.5 rounded-full',
                        t.ambiance === 'TRYHARD'
                          ? 'bg-purple-600/20 text-purple-300'
                          : 'bg-green-600/20 text-green-300',
                      ]"
                    >
                      {{ AMBIANCE_LABELS[t.ambiance] ?? t.ambiance }}
                    </span>
                    <span
                      v-if="t.frequency_min != null && t.frequency_max != null"
                      class="bg-gray-700/50 text-gray-300 text-xs font-medium px-2 py-0.5 rounded-full"
                    >
                      {{ t.frequency_min }}-{{ t.frequency_max }}x / semaine
                    </span>
                  </div>
                  <div class="space-y-1">
                    <template v-for="role in ALL_ROLES" :key="role">
                      <div
                        v-if="teamMembersByRole(t)[role]"
                        class="flex items-center gap-2 bg-gray-700/30 rounded px-2.5 py-1.5"
                      >
                        <img :src="ROLE_ICONS[role]" :alt="role" class="w-5 h-5 opacity-70" />
                        <img
                          v-if="profileIconUrl(teamMembersByRole(t)[role].player.profile_icon_id)"
                          :src="profileIconUrl(teamMembersByRole(t)[role].player.profile_icon_id)"
                          class="w-7 h-7 rounded"
                        />
                        <span class="text-sm font-medium truncate">
                          {{ teamMembersByRole(t)[role].player.riot_game_name
                          }}<span class="text-gray-500">#{{ teamMembersByRole(t)[role].player.riot_tag_line }}</span>
                        </span>
                        <img
                          v-if="teamMembersByRole(t)[role].player.rank_solo_tier"
                          :src="rankIconUrl(teamMembersByRole(t)[role].player.rank_solo_tier!)"
                          class="w-4 h-4"
                        />
                        <span
                          class="text-xs font-semibold"
                          :style="{ color: rankColor(teamMembersByRole(t)[role].player.rank_solo_tier) }"
                        >
                          {{
                            formatRank(
                              teamMembersByRole(t)[role].player.rank_solo_tier,
                              teamMembersByRole(t)[role].player.rank_solo_division,
                            )
                          }}
                        </span>
                        <span
                          v-if="
                            teamMembersByRole(t)[role].player.rank_solo_lp != null &&
                            teamMembersByRole(t)[role].player.rank_solo_tier
                          "
                          class="text-xs"
                          :style="{ color: rankColor(teamMembersByRole(t)[role].player.rank_solo_tier) }"
                        >
                          {{ teamMembersByRole(t)[role].player.rank_solo_lp }} LP
                        </span>
                      </div>
                      <div
                        v-else-if="t.wanted_roles?.includes(role)"
                        class="flex items-center gap-2 border border-dashed border-gray-700 rounded px-2.5 py-1.5"
                      >
                        <img :src="ROLE_ICONS[role]" :alt="role" class="w-5 h-5 opacity-40" />
                        <span class="text-sm text-gray-500 italic">{{ ROLE_LABELS[role] }} recherch&eacute;</span>
                      </div>
                    </template>
                  </div>
                </div>
                <div v-if="t.description" class="w-60 flex-shrink-0 relative hidden sm:block">
                  <div class="absolute inset-0 overflow-y-auto scrollbar-thin bg-gray-700/30 rounded px-3 py-2">
                    <p class="text-xs text-gray-400 uppercase tracking-wide mb-1">Description</p>
                    <p class="text-sm text-gray-300 whitespace-pre-line leading-relaxed">{{ t.description }}</p>
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
              {{ offset + 1 }}-{{ Math.min(offset + PAGE_SIZE, teamTotal) }} sur {{ teamTotal }}
            </span>
            <button
              :disabled="offset + PAGE_SIZE >= teamTotal"
              @click="nextPage"
              class="px-4 py-2 text-sm bg-gray-800 hover:bg-gray-700 disabled:opacity-30 disabled:cursor-default rounded-lg transition"
            >
              Suivant
            </button>
          </div>
        </template>
      </template>
    </div>
  </div>
</template>
