<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { api, type TeamResponse, type TokenInfo } from '@/api/client'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const success = ref('')
const tokenBlocked = ref(false)
const tokenInfo = ref<TokenInfo | null>(null)
const team = ref<TeamResponse | null>(null)
const token = ref('')
const showDeleteConfirm = ref(false)

const teamName = ref('')
const nameError = ref('')
const nameChecking = ref(false)
let nameCheckTimeout: ReturnType<typeof setTimeout> | null = null

const description = ref('')
const activities = ref<string[]>([])
const ambiance = ref('')
const frequencyMin = ref(2)
const frequencyMax = ref(3)
const wantedRoles = ref<string[]>([])
const minRank = ref('')
const maxRank = ref('')
const isLfp = ref(true)

function onNameInput() {
  nameError.value = ''
  if (nameCheckTimeout) clearTimeout(nameCheckTimeout)
  const name = teamName.value.trim()
  if (!name || name.length < 2) {
    nameError.value = name.length > 0 ? 'Le nom doit faire au moins 2 caractères.' : ''
    return
  }
  if (name.length > 50) {
    nameError.value = 'Le nom ne doit pas dépasser 50 caractères.'
    return
  }
  if (name === team.value?.name) return
  nameChecking.value = true
  nameCheckTimeout = setTimeout(async () => {
    try {
      const { available } = await api.checkTeamName(name, team.value?.slug)
      if (teamName.value.trim() === name) {
        nameError.value = available ? '' : 'Ce nom est déjà pris.'
      }
    } catch {
      nameError.value = ''
    } finally {
      nameChecking.value = false
    }
  }, 400)
}

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

const DESC_MAX = 500
const RANK_ORDER = RANK_OPTIONS.map((o) => o.value).filter((v) => v !== '')

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

function validationError(): string {
  const name = teamName.value.trim()
  if (!name || name.length < 2) return 'Le nom doit faire au moins 2 caractères.'
  if (name.length > 50) return 'Le nom ne doit pas dépasser 50 caractères.'
  if (nameError.value) return nameError.value
  if (frequencyMin.value > frequencyMax.value)
    return 'La fréquence min doit être inférieure ou égale à la fréquence max.'
  if (description.value.length > DESC_MAX) return `La description ne doit pas dépasser ${DESC_MAX} caractères.`
  if (minRank.value && maxRank.value && RANK_ORDER.indexOf(minRank.value) > RANK_ORDER.indexOf(maxRank.value))
    return 'Le rang minimum doit être inférieur ou égal au rang maximum.'
  return ''
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
    if (tokenInfo.value.action !== 'team_edit' || !tokenInfo.value.slug) {
      tokenBlocked.value = true
      return
    }
    team.value = await api.getTeam(tokenInfo.value.slug, t)
    teamName.value = team.value.name
    description.value = team.value.description ?? ''
    activities.value = team.value.activities ?? []
    ambiance.value = team.value.ambiance ?? ''
    frequencyMin.value = team.value.frequency_min ?? 2
    frequencyMax.value = team.value.frequency_max ?? 3
    wantedRoles.value = team.value.wanted_roles ?? []
    minRank.value = team.value.min_rank ?? ''
    maxRank.value = team.value.max_rank ?? ''
    isLfp.value = team.value.is_lfp
  } catch {
    tokenBlocked.value = true
  } finally {
    loading.value = false
  }
})

async function saveTeam() {
  if (!team.value) return
  const ve = validationError()
  if (ve) {
    error.value = ve
    return
  }
  saving.value = true
  error.value = ''
  success.value = ''
  try {
    const nameChanged = teamName.value.trim() !== team.value.name
    const updated = await api.updateTeam(
      team.value.slug,
      {
        name: nameChanged ? teamName.value.trim() : undefined,
        description: description.value || undefined,
        activities: activities.value,
        ambiance: ambiance.value || undefined,
        frequency_min: frequencyMin.value,
        frequency_max: frequencyMax.value,
        wanted_roles: wantedRoles.value,
        min_rank: minRank.value || undefined,
        max_rank: maxRank.value || undefined,
        is_lfp: isLfp.value,
      },
      token.value,
    )
    team.value = updated
    success.value = 'Équipe mise à jour !'
  } catch (e: any) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}

async function deleteTeam() {
  if (!team.value) return
  saving.value = true
  error.value = ''
  try {
    await api.deleteTeam(team.value.slug, token.value)
    router.push('/')
  } catch (e: any) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="bg-gray-900 text-white flex items-center justify-center p-4 sm:p-8 flex-1">
    <div class="w-full max-w-lg">
      <h1 class="text-3xl font-bold mb-8 text-center">Modifier mon équipe</h1>

      <div v-if="tokenBlocked" class="bg-gray-800 rounded-xl p-8 text-center">
        <div class="text-4xl mb-4">&#x1F512;</div>
        <h2 class="text-xl font-bold mb-3">Accès réservé</h2>
        <p class="text-gray-400">
          Pour modifier ton équipe, utilise la commande
          <code class="bg-gray-700 px-2 py-0.5 rounded text-indigo-300">/rt-team-edit</code> sur Discord.
        </p>
      </div>

      <div v-else-if="loading" class="text-center text-gray-400">Chargement de l'équipe...</div>

      <div v-else-if="team">
        <div class="bg-gray-800 rounded-xl p-4 mb-6">
          <div class="flex items-center justify-between mb-3">
            <p class="text-sm text-gray-400">{{ team.members.length }}/5 membres</p>
            <RouterLink :to="`/t/${team.slug}`" class="text-sm text-indigo-400 hover:text-indigo-300 transition">
              Voir l'équipe
            </RouterLink>
          </div>
          <label class="block text-sm text-gray-400 mb-1">Nom de l'équipe</label>
          <input
            v-model="teamName"
            type="text"
            maxlength="50"
            class="w-full bg-gray-700 border rounded-lg px-3 py-2 text-white focus:outline-none transition"
            :class="nameError ? 'border-red-500 focus:border-red-500' : 'border-gray-600 focus:border-indigo-500'"
            @input="onNameInput"
          />
          <p v-if="nameChecking" class="text-xs text-gray-500 mt-1">Vérification...</p>
          <p v-else-if="nameError" class="text-xs text-red-400 mt-1">{{ nameError }}</p>
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
                  ambiance === 'TRYHARD' ? 'bg-purple-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700',
                ]"
                @click="ambiance = ambiance === 'TRYHARD' ? '' : 'TRYHARD'"
              >
                Tryhard
              </button>
              <button
                :class="[
                  'flex-1 py-2.5 rounded-lg text-sm font-semibold transition',
                  ambiance === 'FUN' ? 'bg-green-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700',
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
          :disabled="saving || nameChecking || !!nameError"
          class="w-full mt-6 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold py-2.5 rounded-lg transition"
          @click="saveTeam"
        >
          {{ saving ? 'Enregistrement...' : 'Enregistrer' }}
        </button>

        <p v-if="success" class="mt-3 text-green-400 text-sm text-center">{{ success }}</p>
        <p v-if="error" class="mt-3 text-red-400 text-sm text-center">{{ error }}</p>

        <!-- Data export -->
        <div class="mt-10 border border-gray-700 rounded-xl p-5">
          <h3 class="text-gray-300 font-semibold mb-2">Données de l'équipe</h3>
          <p class="text-sm text-gray-400 mb-4">
            Exporte toutes les données de ton équipe au format JSON (droit à la portabilité RGPD).
          </p>
          <a
            :href="api.exportTeam(team.slug, token)"
            download
            class="inline-block bg-gray-700 hover:bg-gray-600 text-white text-sm px-4 py-2.5 rounded-lg transition"
          >
            Exporter les données
          </a>
        </div>

        <!-- Danger zone -->
        <div class="mt-6 border border-red-900/50 rounded-xl p-5">
          <h3 class="text-red-400 font-semibold mb-2">Zone danger</h3>
          <p class="text-sm text-gray-400 mb-4">
            Cette action est irréversible. Ton équipe et toutes ses données seront supprimées.
          </p>
          <button
            v-if="!showDeleteConfirm"
            class="w-full bg-red-900/30 hover:bg-red-900/50 text-red-400 py-2.5 rounded-lg transition"
            @click="showDeleteConfirm = true"
          >
            Supprimer mon équipe
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
              @click="deleteTeam"
            >
              Confirmer la suppression
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
