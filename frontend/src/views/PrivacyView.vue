<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="bg-gray-900 text-white p-4 sm:p-8">
    <div class="max-w-3xl mx-auto">
      <RouterLink to="/" class="text-indigo-400 hover:text-indigo-300 text-sm mb-6 inline-block">&larr; Retour à l'accueil</RouterLink>

      <h1 class="text-3xl font-bold mb-8">Politique de confidentialité</h1>
      <p class="text-gray-400 text-sm mb-8">Dernière mise à jour : 18 février 2026</p>

      <div class="space-y-8 text-gray-300 leading-relaxed">
        <section>
          <h2 class="text-xl font-semibold text-white mb-3">Responsable du traitement</h2>
          <p>Jean Fechter</p>
          <p>Contact : <a href="mailto:jean.fechter@gmail.com" class="text-indigo-400 hover:text-indigo-300">jean.fechter@gmail.com</a></p>
        </section>

        <section>
          <h2 class="text-xl font-semibold text-white mb-3">Données collectées</h2>
          <p class="mb-3">RiftTeam collecte les données suivantes :</p>

          <h3 class="text-lg font-medium text-white mb-2">Données Riot Games (récupérées automatiquement via l'API Riot)</h3>
          <ul class="list-disc list-inside space-y-1 mb-4 text-gray-400">
            <li>Identifiants : PUUID, nom d'invocateur (game name), tag line</li>
            <li>Rang actuel (Solo/Duo et Flex) : tier, division, LP, victoires, défaites</li>
            <li>Maîtrise des champions (top 10) : niveau, points, statistiques récentes</li>
            <li>Rôle principal et secondaire (calculés depuis les derniers matchs)</li>
            <li>Niveau de compte et icône de profil</li>
          </ul>

          <h3 class="text-lg font-medium text-white mb-2">Données Discord</h3>
          <ul class="list-disc list-inside space-y-1 mb-4 text-gray-400">
            <li>Identifiant utilisateur Discord (user ID)</li>
            <li>Nom d'utilisateur Discord</li>
          </ul>

          <h3 class="text-lg font-medium text-white mb-2">Données déclaratives (fournies par le joueur)</h3>
          <ul class="list-disc list-inside space-y-1 text-gray-400">
            <li>Description libre</li>
            <li>Activités recherchées (scrims, tournois, LAN, etc.)</li>
            <li>Ambiance souhaitée (tryhard, for fun)</li>
            <li>Fréquence de jeu</li>
          </ul>
        </section>

        <section>
          <h2 class="text-xl font-semibold text-white mb-3">Base légale</h2>
          <p>Le traitement de vos données repose sur votre <strong class="text-white">consentement explicite</strong>, recueilli lors de la création de votre profil (article 6.1.a du RGPD).</p>
        </section>

        <section>
          <h2 class="text-xl font-semibold text-white mb-3">Finalité du traitement</h2>
          <p>Les données sont collectées dans le but de fournir un profil joueur vérifiable pour la recherche d'équipe dans League of Legends (LFT — Looking for Team).</p>
        </section>

        <section>
          <h2 class="text-xl font-semibold text-white mb-3">Durée de conservation</h2>
          <ul class="list-disc list-inside space-y-1 text-gray-400">
            <li>Les données sont conservées tant que votre profil existe sur la plateforme.</li>
            <li>Des snapshots de données Riot peuvent être conservés pour l'historique statistique.</li>
            <li>En cas de suppression de profil, toutes les données associées sont supprimées en cascade.</li>
          </ul>
        </section>

        <section>
          <h2 class="text-xl font-semibold text-white mb-3">Vos droits</h2>
          <p class="mb-3">Conformément au RGPD, vous disposez des droits suivants :</p>
          <ul class="list-disc list-inside space-y-1 text-gray-400">
            <li><strong class="text-white">Droit d'accès</strong> : obtenir une copie de vos données personnelles</li>
            <li><strong class="text-white">Droit de rectification</strong> : corriger vos données inexactes ou incomplètes</li>
            <li><strong class="text-white">Droit de suppression</strong> : demander l'effacement de vos données</li>
            <li><strong class="text-white">Droit à la portabilité</strong> : recevoir vos données dans un format structuré</li>
          </ul>
          <p class="mt-3">Pour exercer ces droits, contactez : <a href="mailto:jean.fechter@gmail.com" class="text-indigo-400 hover:text-indigo-300">jean.fechter@gmail.com</a></p>
        </section>

        <section>
          <h2 class="text-xl font-semibold text-white mb-3">Données Riot Games</h2>
          <p>Les données Riot Games affichées sur RiftTeam sont publiquement accessibles via l'API officielle de Riot Games. Elles sont récupérées et stockées côté serveur uniquement. Aucune donnée Riot n'est collectée côté client.</p>
        </section>

        <section>
          <h2 class="text-xl font-semibold text-white mb-3">Cookies et trackers</h2>
          <p>RiftTeam n'utilise aucun cookie de tracking ni outil d'analyse tiers. Aucune donnée n'est partagée avec des tiers.</p>
        </section>

        <section>
          <h2 class="text-xl font-semibold text-white mb-3">Hébergement</h2>
          <p>Les données sont hébergées par OVHcloud, 2 rue Kellermann, 59100 Roubaix, France.</p>
        </section>
      </div>
    </div>
  </div>
</template>
