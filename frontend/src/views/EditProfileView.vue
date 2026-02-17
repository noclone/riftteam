<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { api, type PlayerResponse, type TokenInfo } from '@/api/client'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const success = ref('')
const tokenBlocked = ref(false)
const tokenInfo = ref<TokenInfo | null>(null)
const player = ref<PlayerResponse | null>(null)
const token = ref('')
const showDeleteConfirm = ref(false)

const description = ref('')
const activities = ref<string[]>([])
const ambiance = ref('')
const frequencyMin = ref(2)
const frequencyMax = ref(3)
const isLft = ref(true)

const ACTIVITY_OPTIONS = [
  { value: 'SCRIMS', label: 'Scrims' },
  { value: 'TOURNOIS', label: 'Tournois' },
  { value: 'LAN', label: 'LAN' },
  { value: 'FLEX', label: 'Flex' },
  { value: 'CLASH', label: 'Clash' },
]

function toggleActivity(value: string) {
  const idx = activities.value.indexOf(value)
  if (idx >= 0) {
    activities.value.splice(idx, 1)
  } else {
    activities.value.push(value)
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
    if (tokenInfo.value.action !== 'edit' || !tokenInfo.value.slug) {
      tokenBlocked.value = true
      return
    }
    player.value = await api.getPlayer(tokenInfo.value.slug, t)
    description.value = player.value.description ?? ''
    activities.value = player.value.activities ?? []
    ambiance.value = player.value.ambiance ?? ''
    frequencyMin.value = player.value.frequency_min ?? 2
    frequencyMax.value = player.value.frequency_max ?? 3
    isLft.value = player.value.is_lft
  } catch {
    tokenBlocked.value = true
  } finally {
    loading.value = false
  }
})

async function saveProfile() {
  if (!player.value) return
  saving.value = true
  error.value = ''
  success.value = ''
  try {
    await api.updatePlayer(player.value.slug, {
      description: description.value || undefined,
      activities: activities.value,
      ambiance: ambiance.value || undefined,
      frequency_min: frequencyMin.value,
      frequency_max: frequencyMax.value,
      is_lft: isLft.value,
    }, token.value)
    success.value = 'Profil mis à jour !'
  } catch (e: any) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}

async function deleteProfile() {
  if (!player.value) return
  saving.value = true
  error.value = ''
  try {
    await api.deletePlayer(player.value.slug, token.value)
    router.push('/')
  } catch (e: any) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-900 text-white flex items-center justify-center p-4 sm:p-8">
    <div class="w-full max-w-lg">
      <h1 class="text-3xl font-bold mb-8 text-center">Modifier mon profil</h1>

      <!-- Token blocked -->
      <div v-if="tokenBlocked" class="bg-gray-800 rounded-xl p-8 text-center">
        <div class="text-4xl mb-4">&#x1F512;</div>
        <h2 class="text-xl font-bold mb-3">Accès réservé</h2>
        <p class="text-gray-400">
          Pour modifier ton profil, utilise la commande <code class="bg-gray-700 px-2 py-0.5 rounded text-indigo-300">/edit</code> sur Discord.
        </p>
      </div>

      <!-- Loading -->
      <div v-else-if="loading" class="text-center text-gray-400">
        Chargement du profil...
      </div>

      <!-- Edit form -->
      <div v-else-if="player">
        <div class="bg-gray-800 rounded-xl p-4 mb-6 flex items-center justify-between">
          <div>
            <p class="text-lg font-bold">
              {{ player.riot_game_name }}<span class="text-gray-500">#{{ player.riot_tag_line }}</span>
            </p>
            <p class="text-sm text-gray-400">
              Discord : {{ player.discord_username }}
            </p>
          </div>
          <RouterLink
            :to="`/p/${player.slug}`"
            class="text-sm text-indigo-400 hover:text-indigo-300 transition"
          >
            Voir mon profil
          </RouterLink>
        </div>

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

          <!-- LFT toggle -->
          <div class="flex items-center justify-between">
            <label class="text-sm text-gray-400">Looking for team</label>
            <button
              :class="[
                'relative inline-flex h-6 w-11 items-center rounded-full transition',
                isLft ? 'bg-indigo-600' : 'bg-gray-700',
              ]"
              @click="isLft = !isLft"
            >
              <span
                :class="[
                  'inline-block h-4 w-4 rounded-full bg-white transition-transform',
                  isLft ? 'translate-x-6' : 'translate-x-1',
                ]"
              />
            </button>
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

        <button
          :disabled="saving"
          class="w-full mt-6 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold py-2.5 rounded-lg transition"
          @click="saveProfile"
        >
          {{ saving ? 'Enregistrement...' : 'Enregistrer' }}
        </button>

        <p v-if="success" class="mt-3 text-green-400 text-sm text-center">{{ success }}</p>
        <p v-if="error" class="mt-3 text-red-400 text-sm text-center">{{ error }}</p>

        <!-- Danger zone -->
        <div class="mt-10 border border-red-900/50 rounded-xl p-5">
          <h3 class="text-red-400 font-semibold mb-2">Zone danger</h3>
          <p class="text-sm text-gray-400 mb-4">
            Cette action est irréversible. Ton profil et toutes tes données seront supprimés.
          </p>
          <button
            v-if="!showDeleteConfirm"
            class="w-full bg-red-900/30 hover:bg-red-900/50 text-red-400 py-2.5 rounded-lg transition"
            @click="showDeleteConfirm = true"
          >
            Supprimer mon profil
          </button>
          <div v-else class="flex gap-3">
            <button
              class="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-2.5 rounded-lg transition"
              @click="showDeleteConfirm = false"
            >
              Annuler
            </button>
            <button
              :disabled="saving"
              class="flex-1 bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white font-semibold py-2.5 rounded-lg transition"
              @click="deleteProfile"
            >
              Confirmer la suppression
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
