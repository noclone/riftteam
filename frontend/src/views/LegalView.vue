<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="bg-gray-900 text-white p-4 sm:p-8">
    <div class="max-w-3xl mx-auto">
      <RouterLink to="/" class="text-indigo-400 hover:text-indigo-300 text-sm mb-6 inline-block">&larr; Retour à l'accueil</RouterLink>

      <h1 class="text-3xl font-bold mb-8">Mentions légales</h1>

      <div class="space-y-8 text-gray-300 leading-relaxed">
        <section>
          <h2 class="text-xl font-semibold text-white mb-3">Éditeur du site</h2>
          <p>Jean Fechter</p>
          <p>Contact : <a href="mailto:jean.fechter@gmail.com" class="text-indigo-400 hover:text-indigo-300">jean.fechter@gmail.com</a></p>
          <p>Site : riftteam.fr</p>
        </section>

        <section>
          <h2 class="text-xl font-semibold text-white mb-3">Hébergeur</h2>
          <p>OVHcloud</p>
          <p>2 rue Kellermann, 59100 Roubaix, France</p>
          <p>Site : <a href="https://www.ovhcloud.com" class="text-indigo-400 hover:text-indigo-300" target="_blank" rel="noopener noreferrer">www.ovhcloud.com</a></p>
        </section>

      </div>
    </div>
  </div>
</template>
