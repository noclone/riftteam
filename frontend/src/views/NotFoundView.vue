<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="bg-gray-900 text-white flex flex-col items-center justify-center p-8 flex-1">
    <p class="text-6xl font-bold text-gray-700 mb-4">404</p>
    <h1 class="text-2xl font-bold mb-2">Page introuvable</h1>
    <p class="text-gray-400 mb-8">Cette page n'existe pas ou a été déplacée.</p>
    <RouterLink
      to="/"
      class="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2.5 px-6 rounded-lg transition"
    >
      Retour à l'accueil
    </RouterLink>
  </div>
</template>
