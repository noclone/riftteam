<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { api, type RiotCheckResponse, type PlayerResponse, type TokenInfo } from '@/api/client'

const route = useRoute()
const step = ref(0)
const loading = ref(false)
const error = ref('')
const tokenBlocked = ref(false)
const tokenInfo = ref<TokenInfo | null>(null)
const riotData = ref<RiotCheckResponse | null>(null)
const createdPlayer = ref<PlayerResponse | null>(null)
const profileUrl = ref('')
const token = ref('')

const DDRAGON_VERSION = ref('15.3.1')
const isClaim = ref(false)

const description = ref('')
const activities = ref<string[]>([])
const ambiance = ref('')
const frequencyMin = ref(2)
const frequencyMax = ref(3)
const consentAccepted = ref(false)

const ACTIVITY_OPTIONS = [
  { value: 'SCRIMS', label: 'Scrims' },
  { value: 'TOURNOIS', label: 'Tournois' },
  { value: 'LAN', label: 'LAN' },
  { value: 'FLEX', label: 'Flex' },
  { value: 'CLASH', label: 'Clash' },
]

const DESC_MAX = 500

function toggleActivity(value: string) {
  const idx = activities.value.indexOf(value)
  if (idx >= 0) {
    activities.value.splice(idx, 1)
  } else {
    activities.value.push(value)
  }
}

function validationError(): string {
  if (frequencyMin.value > frequencyMax.value) return 'La fréquence min doit être inférieure ou égale à la fréquence max.'
  if (description.value.length > DESC_MAX) return `La description ne doit pas dépasser ${DESC_MAX} caractères.`
  return ''
}

function profileIconUrl(iconId: number | null): string {
  if (!iconId) return ''
  return `https://ddragon.leagueoflegends.com/cdn/${DDRAGON_VERSION.value}/img/profileicon/${iconId}.png`
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
  const t = route.query.token as string | undefined
  if (!t) {
    tokenBlocked.value = true
    return
  }
  token.value = t
  loading.value = true
  try {
    tokenInfo.value = await api.validateToken(t)
    if (tokenInfo.value.action !== 'create' || !tokenInfo.value.game_name || !tokenInfo.value.tag_line) {
      tokenBlocked.value = true
      return
    }
    await fetchDDragonVersion()
    riotData.value = await api.checkRiotId(tokenInfo.value.game_name, tokenInfo.value.tag_line)
    const slug = `${tokenInfo.value.game_name}-${tokenInfo.value.tag_line}`
    try {
      const existing = await api.getPlayer(slug)
      if (existing && existing.discord_user_id === null) {
        isClaim.value = true
      }
    } catch {
      // player doesn't exist, normal create flow
    }
    step.value = 1
  } catch {
    tokenBlocked.value = true
  } finally {
    loading.value = false
  }
})

async function createProfile() {
  if (!riotData.value) return
  const ve = validationError()
  if (ve) { error.value = ve; return }
  loading.value = true
  error.value = ''
  try {
    const player = await api.createPlayer({
      description: description.value || undefined,
      activities: activities.value.length > 0 ? activities.value : undefined,
      ambiance: ambiance.value || undefined,
      frequency_min: frequencyMin.value,
      frequency_max: frequencyMax.value,
    }, token.value)
    createdPlayer.value = player
    profileUrl.value = `${window.location.origin}/p/${player.slug}`
    step.value = 3
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="bg-gray-900 text-white flex items-center justify-center p-4 sm:p-8 flex-1">
    <div class="w-full max-w-lg">
      <h1 class="text-3xl font-bold mb-8 text-center">Créer mon profil</h1>

      <!-- Token blocked -->
      <div v-if="tokenBlocked" class="bg-gray-800 rounded-xl p-8 text-center">
        <div class="text-4xl mb-4">&#x1F512;</div>
        <h2 class="text-xl font-bold mb-3">Accès réservé</h2>
        <p class="text-gray-400">
          Pour créer ton profil, utilise la commande <code class="bg-gray-700 px-2 py-0.5 rounded text-indigo-300">/rt-profil-create Pseudo#TAG</code> sur Discord.
        </p>
      </div>

      <!-- Loading token validation -->
      <div v-else-if="loading && step === 0" class="text-center text-gray-400">
        Vérification en cours...
      </div>

      <template v-else>
        <!-- Steps indicator -->
        <div v-if="step <= 2" class="flex items-center justify-center gap-2 mb-8">
          <div
            v-for="s in 2"
            :key="s"
            :class="[
              'w-8 h-1 rounded-full transition',
              s <= step ? 'bg-indigo-500' : 'bg-gray-700',
            ]"
          />
        </div>

        <!-- Step 1: Confirmation with Riot preview -->
        <div v-if="step === 1 && riotData">
          <div class="bg-gray-800 rounded-xl p-6 mb-6">
            <div class="flex items-center gap-4 mb-4">
              <img
                v-if="profileIconUrl(riotData.profile_icon_id)"
                :src="profileIconUrl(riotData.profile_icon_id)"
                :alt="riotData.game_name"
                class="w-16 h-16 rounded-xl"
              />
              <div>
                <p class="text-xl font-bold">{{ riotData.game_name }}<span class="text-gray-500">#{{ riotData.tag_line }}</span></p>
                <p v-if="riotData.summoner_level" class="text-gray-400 text-sm">
                  Niveau {{ riotData.summoner_level }}
                </p>
              </div>
            </div>
            <p class="text-sm text-gray-400">
              Le profil complet (rang, champions, rôle) sera récupéré automatiquement via l'API Riot.
            </p>
          </div>
          <button
            class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2.5 rounded-lg transition"
            @click="step = 2"
          >
            C'est bien moi
          </button>
        </div>

        <!-- Step 2: Declarative info (no Discord field) -->
        <div v-if="step === 2">
          <div class="space-y-5">
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

            <div>
              <label class="block text-sm text-gray-400 mb-1">Description</label>
              <textarea
                v-model="description"
                rows="3"
                placeholder="Parle de toi, de ton style de jeu..."
                class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-white focus:border-indigo-500 focus:outline-none transition"
              />
            </div>
          </div>
          <label class="flex items-start gap-2 mt-6 cursor-pointer">
            <input
              v-model="consentAccepted"
              type="checkbox"
              class="mt-1 accent-indigo-600"
            />
            <span class="text-sm text-gray-400">
              En créant mon profil, j'accepte la
              <RouterLink to="/privacy" class="text-indigo-400 hover:text-indigo-300 underline" target="_blank">politique de confidentialité</RouterLink>.
            </span>
          </label>
          <div class="flex gap-3 mt-4">
            <button
              class="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-2.5 rounded-lg transition"
              @click="step = 1"
            >
              Retour
            </button>
            <button
              :disabled="loading || !consentAccepted"
              class="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold py-2.5 rounded-lg transition"
              @click="createProfile"
            >
              {{ loading ? 'Création...' : 'Créer mon profil' }}
            </button>
          </div>
        </div>

        <!-- Step 3: Success -->
        <div v-if="step === 3 && createdPlayer" class="text-center">
          <div class="bg-gray-800 rounded-xl p-8 mb-6">
            <div class="text-4xl mb-4">&#x2705;</div>
            <h2 class="text-2xl font-bold mb-2">{{ isClaim ? 'Profil attribué !' : 'Profil créé !' }}</h2>
            <p class="text-gray-400 mb-6">Ton profil est prêt à être partagé.</p>

            <div class="bg-gray-700/50 rounded-lg p-4 mb-6">
              <p class="text-sm text-gray-400 mb-1">Ton lien</p>
              <p class="font-mono text-indigo-300 break-all">
                {{ profileUrl }}
              </p>
            </div>

            <div class="flex gap-3 justify-center">
              <RouterLink
                :to="`/p/${createdPlayer.slug}`"
                class="bg-gray-700 hover:bg-gray-600 text-white px-6 py-2.5 rounded-lg transition"
              >
                Voir mon profil
              </RouterLink>
            </div>
          </div>

          <p class="text-sm text-gray-500">
            Colle ce lien dans Discord pour un embed riche avec ton rang et tes champions.
          </p>
        </div>
      </template>

      <p v-if="error" class="mt-4 text-red-400 text-sm text-center">{{ error }}</p>
    </div>
  </div>
</template>
