<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api, type RiotCheckResponse, type PlayerResponse } from '@/api/client'

const step = ref(1)
const gameName = ref('')
const tagLine = ref('')
const loading = ref(false)
const error = ref('')
const riotData = ref<RiotCheckResponse | null>(null)
const createdPlayer = ref<PlayerResponse | null>(null)
const linkCopied = ref(false)
const profileUrl = ref('')

const DDRAGON_VERSION = ref('15.3.1')

const discordUsername = ref('')
const description = ref('')
const lookingFor = ref('TEAM')
const ambition = ref('COMPETITIVE')
const languages = ref<string[]>(['fr'])

const DAYS = [
  { key: 'monday', label: 'Lun' },
  { key: 'tuesday', label: 'Mar' },
  { key: 'wednesday', label: 'Mer' },
  { key: 'thursday', label: 'Jeu' },
  { key: 'friday', label: 'Ven' },
  { key: 'saturday', label: 'Sam' },
  { key: 'sunday', label: 'Dim' },
]
const SLOTS = ['Matin', 'Après-midi', 'Soir', 'Nuit']
const availability = ref<Record<string, string[]>>({})

const LANGUAGE_OPTIONS = [
  { value: 'fr', label: 'Français' },
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Español' },
  { value: 'de', label: 'Deutsch' },
  { value: 'pt', label: 'Português' },
  { value: 'it', label: 'Italiano' },
]

function toggleSlot(day: string, slot: string) {
  if (!availability.value[day]) {
    availability.value[day] = [slot]
    return
  }
  const idx = availability.value[day].indexOf(slot)
  if (idx >= 0) {
    availability.value[day].splice(idx, 1)
    if (availability.value[day].length === 0) {
      delete availability.value[day]
    }
  } else {
    availability.value[day].push(slot)
  }
}

function isSlotActive(day: string, slot: string): boolean {
  return availability.value[day]?.includes(slot) ?? false
}

function toggleLang(lang: string) {
  const idx = languages.value.indexOf(lang)
  if (idx >= 0) {
    if (languages.value.length > 1) languages.value.splice(idx, 1)
  } else {
    languages.value.push(lang)
  }
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

async function searchRiotId() {
  if (!gameName.value || !tagLine.value) return
  loading.value = true
  error.value = ''
  await fetchDDragonVersion()
  try {
    riotData.value = await api.checkRiotId(gameName.value, tagLine.value)
    step.value = 2
  } catch (e: any) {
    error.value = e.status === 404 ? 'Riot ID introuvable.' : e.message
  } finally {
    loading.value = false
  }
}

async function createProfile() {
  if (!riotData.value) return
  loading.value = true
  error.value = ''
  try {
    const avail = Object.keys(availability.value).length > 0 ? availability.value : undefined
    const player = await api.createPlayer({
      game_name: riotData.value.game_name,
      tag_line: riotData.value.tag_line,
      discord_username: discordUsername.value || undefined,
      description: description.value || undefined,
      looking_for: lookingFor.value,
      ambition: ambition.value,
      languages: languages.value,
      availability: avail,
    })
    createdPlayer.value = player
    profileUrl.value = `${window.location.origin}/p/${player.slug}`
    step.value = 4
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function copyLink() {
  if (!createdPlayer.value) return
  const url = `${window.location.origin}/p/${createdPlayer.value.slug}`
  await navigator.clipboard.writeText(url)
  linkCopied.value = true
  setTimeout(() => { linkCopied.value = false }, 2000)
}
</script>

<template>
  <div class="min-h-screen bg-gray-900 text-white flex items-center justify-center p-4 sm:p-8">
    <div class="w-full max-w-lg">
      <h1 class="text-3xl font-bold mb-8 text-center">Créer mon profil</h1>

      <!-- Steps indicator -->
      <div v-if="step <= 3" class="flex items-center justify-center gap-2 mb-8">
        <div
          v-for="s in 3"
          :key="s"
          :class="[
            'w-8 h-1 rounded-full transition',
            s <= step ? 'bg-indigo-500' : 'bg-gray-700',
          ]"
        />
      </div>

      <!-- Step 1: Riot ID -->
      <div v-if="step === 1">
        <label class="block text-sm text-gray-400 mb-2">Ton Riot ID</label>
        <div class="flex gap-2 mb-4">
          <input
            v-model="gameName"
            placeholder="Pseudo"
            class="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-white focus:border-indigo-500 focus:outline-none transition"
            @keyup.enter="searchRiotId"
          />
          <span class="text-gray-500 self-center text-lg">#</span>
          <input
            v-model="tagLine"
            placeholder="TAG"
            class="w-24 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-white focus:border-indigo-500 focus:outline-none transition"
            @keyup.enter="searchRiotId"
          />
        </div>
        <button
          :disabled="loading || !gameName || !tagLine"
          class="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold py-2.5 rounded-lg transition"
          @click="searchRiotId"
        >
          {{ loading ? 'Recherche...' : 'Rechercher' }}
        </button>
      </div>

      <!-- Step 2: Confirmation with rank/role/champs preview -->
      <div v-if="step === 2 && riotData">
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
        <div class="flex gap-3">
          <button
            class="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-2.5 rounded-lg transition"
            @click="step = 1"
          >
            Retour
          </button>
          <button
            class="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2.5 rounded-lg transition"
            @click="step = 3"
          >
            C'est bien moi
          </button>
        </div>
      </div>

      <!-- Step 3: Declarative info -->
      <div v-if="step === 3">
        <div class="space-y-5">
          <div>
            <label class="block text-sm text-gray-400 mb-1">Discord</label>
            <input
              v-model="discordUsername"
              placeholder="pseudo"
              class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-white focus:border-indigo-500 focus:outline-none transition"
            />
          </div>
          <div>
            <label class="block text-sm text-gray-400 mb-1">Tu cherches</label>
            <select
              v-model="lookingFor"
              class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-white"
            >
              <option value="TEAM">Une équipe</option>
              <option value="DUO">Un duo</option>
              <option value="CLASH">Clash</option>
              <option value="SCRIM">Scrims</option>
              <option value="ANY">Tout</option>
            </select>
          </div>
          <div>
            <label class="block text-sm text-gray-400 mb-1">Ambition</label>
            <select
              v-model="ambition"
              class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-white"
            >
              <option value="CHILL">Chill</option>
              <option value="IMPROVE">Progresser</option>
              <option value="COMPETITIVE">Compétitif</option>
              <option value="TRYHARD">Tryhard</option>
            </select>
          </div>

          <!-- Languages -->
          <div>
            <label class="block text-sm text-gray-400 mb-2">Langues</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="lang in LANGUAGE_OPTIONS"
                :key="lang.value"
                :class="[
                  'px-3 py-1.5 rounded-lg text-sm transition',
                  languages.includes(lang.value)
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700',
                ]"
                @click="toggleLang(lang.value)"
              >
                {{ lang.label }}
              </button>
            </div>
          </div>

          <!-- Availability grid -->
          <div>
            <label class="block text-sm text-gray-400 mb-2">Disponibilités</label>
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr>
                    <th class="text-left text-gray-500 font-normal pb-2 pr-2"></th>
                    <th v-for="day in DAYS" :key="day.key" class="text-center text-gray-500 font-normal pb-2 px-1">
                      {{ day.label }}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="slot in SLOTS" :key="slot">
                    <td class="text-gray-400 pr-2 py-1 whitespace-nowrap">{{ slot }}</td>
                    <td v-for="day in DAYS" :key="day.key" class="text-center px-1 py-1">
                      <button
                        :class="[
                          'w-8 h-8 rounded transition',
                          isSlotActive(day.key, slot)
                            ? 'bg-indigo-600'
                            : 'bg-gray-800 hover:bg-gray-700',
                        ]"
                        @click="toggleSlot(day.key, slot)"
                      />
                    </td>
                  </tr>
                </tbody>
              </table>
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
        <div class="flex gap-3 mt-6">
          <button
            class="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-2.5 rounded-lg transition"
            @click="step = 2"
          >
            Retour
          </button>
          <button
            :disabled="loading"
            class="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold py-2.5 rounded-lg transition"
            @click="createProfile"
          >
            {{ loading ? 'Création...' : 'Créer mon profil' }}
          </button>
        </div>
      </div>

      <!-- Step 4: Success -->
      <div v-if="step === 4 && createdPlayer" class="text-center">
        <div class="bg-gray-800 rounded-xl p-8 mb-6">
          <div class="text-4xl mb-4">&#x2705;</div>
          <h2 class="text-2xl font-bold mb-2">Profil créé !</h2>
          <p class="text-gray-400 mb-6">Ton profil est prêt à être partagé.</p>

          <div class="bg-gray-700/50 rounded-lg p-4 mb-6">
            <p class="text-sm text-gray-400 mb-1">Ton lien</p>
            <p class="font-mono text-indigo-300 break-all">
              {{ profileUrl }}
            </p>
          </div>

          <div class="flex gap-3 justify-center">
            <button
              @click="copyLink"
              class="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-6 py-2.5 rounded-lg transition"
            >
              {{ linkCopied ? 'Copié !' : 'Copier le lien' }}
            </button>
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

      <p v-if="error" class="mt-4 text-red-400 text-sm text-center">{{ error }}</p>
    </div>
  </div>
</template>
