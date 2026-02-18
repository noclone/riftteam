<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { api, type TeamResponse, type TokenInfo } from '@/api/client'

const route = useRoute()
const loading = ref(false)
const error = ref('')
const tokenBlocked = ref(false)
const tokenInfo = ref<TokenInfo | null>(null)
const createdTeam = ref<TeamResponse | null>(null)
const teamUrl = ref('')
const token = ref('')

const description = ref('')
const activities = ref<string[]>([])
const ambiance = ref('')
const frequencyMin = ref(2)
const frequencyMax = ref(3)
const wantedRoles = ref<string[]>([])
const minRank = ref('')
const maxRank = ref('')
const isLfp = ref(true)

const ACTIVITY_OPTIONS = [
  { value: 'SCRIMS', label: 'Scrims' },
  { value: 'TOURNOIS', label: 'Tournois' },
  { value: 'LAN', label: 'LAN' },
  { value: 'FLEX', label: 'Flex' },
  { value: 'CLASH', label: 'Clash' },
]

const ROLE_OPTIONS = [
  { value: 'TOP', label: 'Top' },
  { value: 'JUNGLE', label: 'Jungle' },
  { value: 'MIDDLE', label: 'Mid' },
  { value: 'BOTTOM', label: 'ADC' },
  { value: 'UTILITY', label: 'Support' },
]

const RANK_OPTIONS = [
  { value: '', label: 'Aucun' },
  { value: 'IRON', label: 'Iron' },
  { value: 'BRONZE', label: 'Bronze' },
  { value: 'SILVER', label: 'Silver' },
  { value: 'GOLD', label: 'Gold' },
  { value: 'PLATINUM', label: 'Platinum' },
  { value: 'EMERALD', label: 'Emerald' },
  { value: 'DIAMOND', label: 'Diamond' },
  { value: 'MASTER', label: 'Master' },
  { value: 'GRANDMASTER', label: 'Grandmaster' },
  { value: 'CHALLENGER', label: 'Challenger' },
]

function toggleActivity(value: string) {
  const idx = activities.value.indexOf(value)
  if (idx >= 0) activities.value.splice(idx, 1)
  else activities.value.push(value)
}

function toggleRole(value: string) {
  const idx = wantedRoles.value.indexOf(value)
  if (idx >= 0) wantedRoles.value.splice(idx, 1)
  else wantedRoles.value.push(value)
}

onMounted(async () => {
  const t = route.query.token as string | undefined
  if (!t) {
    tokenBlocked.value = true
    return
  }
  token.value = t
  loading.value = true
  try {
    tokenInfo.value = await api.validateToken(t)
    if (tokenInfo.value.action !== 'team_create' || !tokenInfo.value.team_name) {
      tokenBlocked.value = true
      return
    }
  } catch {
    tokenBlocked.value = true
  } finally {
    loading.value = false
  }
})

async function createTeam() {
  loading.value = true
  error.value = ''
  try {
    const team = await api.createTeam({
      description: description.value || undefined,
      activities: activities.value.length > 0 ? activities.value : undefined,
      ambiance: ambiance.value || undefined,
      frequency_min: frequencyMin.value,
      frequency_max: frequencyMax.value,
      wanted_roles: wantedRoles.value.length > 0 ? wantedRoles.value : undefined,
      min_rank: minRank.value || undefined,
      max_rank: maxRank.value || undefined,
      is_lfp: isLfp.value,
    }, token.value)
    createdTeam.value = team
    teamUrl.value = `${window.location.origin}/t/${team.slug}`
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-900 text-white flex items-center justify-center p-4 sm:p-8">
    <div class="w-full max-w-lg">
      <h1 class="text-3xl font-bold mb-8 text-center">Créer mon équipe</h1>

      <div v-if="tokenBlocked" class="bg-gray-800 rounded-xl p-8 text-center">
        <div class="text-4xl mb-4">&#x1F512;</div>
        <h2 class="text-xl font-bold mb-3">Accès réservé</h2>
        <p class="text-gray-400">
          Pour créer une équipe, utilise la commande <code class="bg-gray-700 px-2 py-0.5 rounded text-indigo-300">/rt-team-create NomEquipe</code> sur Discord.
        </p>
      </div>

      <div v-else-if="loading && !tokenInfo" class="text-center text-gray-400">
        Vérification en cours...
      </div>

      <template v-else-if="!createdTeam && tokenInfo">
        <div class="bg-gray-800 rounded-xl p-4 mb-6">
          <p class="text-lg font-bold">{{ tokenInfo.team_name }}</p>
          <p class="text-sm text-gray-400">Capitaine : {{ tokenInfo.discord_username }}</p>
        </div>

        <div class="space-y-5">
          <!-- Rôles recherchés -->
          <div>
            <label class="block text-sm text-gray-400 mb-2">Rôles recherchés</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="opt in ROLE_OPTIONS"
                :key="opt.value"
                :class="[
                  'px-3 py-1.5 rounded-lg text-sm transition',
                  wantedRoles.includes(opt.value)
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700',
                ]"
                @click="toggleRole(opt.value)"
              >
                {{ opt.label }}
              </button>
            </div>
          </div>

          <!-- Elo range -->
          <div>
            <label class="block text-sm text-gray-400 mb-2">Range d'elo</label>
            <div class="flex items-center gap-2">
              <select
                v-model="minRank"
                class="bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-white text-sm flex-1"
              >
                <option v-for="opt in RANK_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
              <span class="text-gray-400 text-sm">→</span>
              <select
                v-model="maxRank"
                class="bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-white text-sm flex-1"
              >
                <option v-for="opt in RANK_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </div>
          </div>

          <!-- Objectifs -->
          <div>
            <label class="block text-sm text-gray-400 mb-2">Objectifs</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="opt in ACTIVITY_OPTIONS"
                :key="opt.value"
                :class="[
                  'px-3 py-1.5 rounded-lg text-sm transition',
                  activities.includes(opt.value)
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700',
                ]"
                @click="toggleActivity(opt.value)"
              >
                {{ opt.label }}
              </button>
            </div>
          </div>

          <!-- Ambiance -->
          <div>
            <label class="block text-sm text-gray-400 mb-2">Ambiance</label>
            <div class="flex gap-2">
              <button
                :class="[
                  'flex-1 py-2.5 rounded-lg text-sm font-semibold transition',
                  ambiance === 'TRYHARD'
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700',
                ]"
                @click="ambiance = ambiance === 'TRYHARD' ? '' : 'TRYHARD'"
              >
                Tryhard
              </button>
              <button
                :class="[
                  'flex-1 py-2.5 rounded-lg text-sm font-semibold transition',
                  ambiance === 'FUN'
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700',
                ]"
                @click="ambiance = ambiance === 'FUN' ? '' : 'FUN'"
              >
                For fun
              </button>
            </div>
          </div>

          <!-- Frequency -->
          <div>
            <label class="block text-sm text-gray-400 mb-2">Fréquence</label>
            <div class="flex items-center gap-2">
              <span class="text-gray-400 text-sm">Entre</span>
              <select
                v-model.number="frequencyMin"
                class="bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-white text-sm"
              >
                <option v-for="n in 7" :key="n" :value="n">{{ n }}</option>
              </select>
              <span class="text-gray-400 text-sm">et</span>
              <select
                v-model.number="frequencyMax"
                class="bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-white text-sm"
              >
                <option v-for="n in 7" :key="n" :value="n">{{ n }}</option>
              </select>
              <span class="text-gray-400 text-sm">fois par semaine</span>
            </div>
          </div>

          <!-- LFP toggle -->
          <div class="flex items-center justify-between">
            <label class="text-sm text-gray-400">Looking for players</label>
            <button
              :class="[
                'relative inline-flex h-6 w-11 items-center rounded-full transition',
                isLfp ? 'bg-indigo-600' : 'bg-gray-700',
              ]"
              @click="isLfp = !isLfp"
            >
              <span
                :class="[
                  'inline-block h-4 w-4 rounded-full bg-white transition-transform',
                  isLfp ? 'translate-x-6' : 'translate-x-1',
                ]"
              />
            </button>
          </div>

          <div>
            <label class="block text-sm text-gray-400 mb-1">Description</label>
            <textarea
              v-model="description"
              rows="3"
              placeholder="Décris ton équipe, ce que vous cherchez..."
              class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-white focus:border-indigo-500 focus:outline-none transition"
            />
          </div>
        </div>

        <button
          :disabled="loading"
          class="w-full mt-6 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold py-2.5 rounded-lg transition"
          @click="createTeam"
        >
          {{ loading ? 'Création...' : 'Créer mon équipe' }}
        </button>
      </template>

      <!-- Success -->
      <div v-if="createdTeam" class="text-center">
        <div class="bg-gray-800 rounded-xl p-8 mb-6">
          <div class="text-4xl mb-4">&#x2705;</div>
          <h2 class="text-2xl font-bold mb-2">Équipe créée !</h2>
          <p class="text-gray-400 mb-6">Ton équipe est prête. Ajoute des membres avec <code class="bg-gray-700 px-2 py-0.5 rounded text-indigo-300">/rt-team-roster add</code> sur Discord.</p>

          <div class="bg-gray-700/50 rounded-lg p-4 mb-6">
            <p class="text-sm text-gray-400 mb-1">Ton lien</p>
            <p class="font-mono text-indigo-300 break-all">{{ teamUrl }}</p>
          </div>

          <div class="flex gap-3 justify-center">
            <RouterLink
              :to="`/t/${createdTeam.slug}`"
              class="bg-gray-700 hover:bg-gray-600 text-white px-6 py-2.5 rounded-lg transition"
            >
              Voir mon équipe
            </RouterLink>
          </div>
        </div>
      </div>

      <p v-if="error" class="mt-4 text-red-400 text-sm text-center">{{ error }}</p>
    </div>
  </div>
</template>
