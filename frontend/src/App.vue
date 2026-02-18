<script setup lang="ts">
import { RouterView, RouterLink } from 'vue-router'
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-900">
    <RouterView class="flex-1" />
    <footer class="bg-gray-900 border-t border-gray-800 px-4 py-6 text-center text-xs text-gray-500 leading-relaxed">
      <p>RiftTeam n'est pas approuvé par Riot Games et ne reflète pas les vues ou opinions de Riot Games ou de quiconque impliqué officiellement dans la production ou la gestion des propriétés de Riot Games.</p>
      <p class="mt-1">Riot Games et toutes les propriétés associées sont des marques déposées ou des marques de commerce enregistrées de Riot Games, Inc.</p>
      <div class="mt-3 flex justify-center gap-4 text-gray-500">
        <RouterLink to="/terms" class="hover:text-gray-400 transition">CGU</RouterLink>
        <RouterLink to="/privacy" class="hover:text-gray-400 transition">Confidentialité</RouterLink>
        <RouterLink to="/legal" class="hover:text-gray-400 transition">Mentions légales</RouterLink>
      </div>
    </footer>
  </div>
</template>
