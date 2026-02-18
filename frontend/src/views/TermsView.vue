<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="bg-gray-900 text-white p-4 sm:p-8">
    <div class="max-w-3xl mx-auto">
      <RouterLink to="/" class="text-indigo-400 hover:text-indigo-300 text-sm mb-6 inline-block">&larr; Retour à l'accueil</RouterLink>

      <h1 class="text-3xl font-bold mb-8">Conditions Générales d'Utilisation</h1>
      <p class="text-gray-400 text-sm mb-8">Dernière mise à jour : 18 février 2026</p>

      <div class="space-y-8 text-gray-300 leading-relaxed">
        <section>
          <h2 class="text-xl font-semibold text-white mb-3">1. Objet</h2>
          <p>Les présentes Conditions Générales d'Utilisation (CGU) régissent l'accès et l'utilisation de la plateforme RiftTeam (ci-après « le Service »), accessible à l'adresse riftteam.fr et via le bot Discord associé.</p>
          <p class="mt-2">RiftTeam est un service gratuit permettant aux joueurs de League of Legends de créer un profil joueur vérifiable et de rechercher des équipes pour des parties organisées (scrims, tournois, clash, etc.).</p>
        </section>

        <section>
          <h2 class="text-xl font-semibold text-white mb-3">2. Accès au Service</h2>
          <p>La création d'un profil nécessite :</p>
          <ul class="list-disc list-inside space-y-1 mt-2 text-gray-400">
            <li>Un compte Discord valide</li>
            <li>Un compte League of Legends avec un Riot ID existant</li>
            <li>L'acceptation des présentes CGU et de la <RouterLink to="/privacy" class="text-indigo-400 hover:text-indigo-300 underline">politique de confidentialité</RouterLink></li>
          </ul>
          <p class="mt-2">L'accès au Service est gratuit. Aucun abonnement ni paiement n'est requis.</p>
        </section>

        <section>
          <h2 class="text-xl font-semibold text-white mb-3">3. Responsabilités de l'utilisateur</h2>
          <p>L'utilisateur s'engage à :</p>
          <ul class="list-disc list-inside space-y-1 mt-2 text-gray-400">
            <li>Ne pas utiliser le Service à des fins illicites ou contraires aux bonnes moeurs</li>
            <li>Ne pas publier de contenu offensant, discriminatoire, diffamatoire ou illégal dans les descriptions de profil ou d'équipe</li>
            <li>Ne pas tenter de perturber le fonctionnement du Service (spam, attaques, scraping abusif)</li>
            <li>Ne pas usurper l'identité d'un autre joueur</li>
          </ul>
          <p class="mt-2">RiftTeam se réserve le droit de supprimer tout profil ou contenu en violation de ces règles, sans préavis.</p>
        </section>

        <section>
          <h2 class="text-xl font-semibold text-white mb-3">4. Données et API Riot Games</h2>
          <p>Les données de jeu affichées sur RiftTeam (rang, champions, statistiques) sont récupérées automatiquement via l'API officielle de Riot Games. Ces données sont publiquement accessibles et ne constituent pas des données personnelles au sens du RGPD.</p>
          <p class="mt-2">RiftTeam ne vérifie pas que l'utilisateur est propriétaire du compte Riot revendiqué. L'utilisateur est responsable de l'exactitude des informations qu'il fournit.</p>
          <p class="mt-2">RiftTeam n'est pas approuvé par Riot Games et ne reflète pas les vues ou opinions de Riot Games ou de quiconque impliqué officiellement dans la production ou la gestion des propriétés de Riot Games. Riot Games et toutes les propriétés associées sont des marques déposées ou des marques de commerce enregistrées de Riot Games, Inc.</p>
        </section>

        <section>
          <h2 class="text-xl font-semibold text-white mb-3">5. Propriété intellectuelle</h2>
          <p>Le code source, le design et le contenu original de RiftTeam sont la propriété de l'éditeur.</p>
          <p class="mt-2">Les noms, logos et images liés à League of Legends sont la propriété de Riot Games, Inc. et sont utilisés conformément aux conditions d'utilisation de l'API Riot Games.</p>
        </section>

        <section>
          <h2 class="text-xl font-semibold text-white mb-3">6. Suppression de compte</h2>
          <p>L'utilisateur peut à tout moment supprimer son profil depuis la page d'édition accessible via la commande Discord <code class="bg-gray-700 px-2 py-0.5 rounded text-indigo-300">/rt-profil-edit</code>. La suppression entraîne l'effacement définitif et irréversible de toutes les données associées.</p>
          <p class="mt-2">L'utilisateur peut également exercer son droit de suppression en contactant <a href="mailto:jean.fechter@gmail.com" class="text-indigo-400 hover:text-indigo-300">jean.fechter@gmail.com</a>.</p>
        </section>

        <section>
          <h2 class="text-xl font-semibold text-white mb-3">7. Limitation de responsabilité</h2>
          <p>RiftTeam est fourni « en l'état », sans garantie de disponibilité, d'exactitude des données ou de résultat. L'éditeur ne saurait être tenu responsable :</p>
          <ul class="list-disc list-inside space-y-1 mt-2 text-gray-400">
            <li>Des interruptions de service, temporaires ou définitives</li>
            <li>De l'inexactitude des données récupérées via l'API Riot Games</li>
            <li>Des interactions entre utilisateurs facilitées par le Service</li>
            <li>De la perte de données en cas de défaillance technique</li>
          </ul>
        </section>

        <section>
          <h2 class="text-xl font-semibold text-white mb-3">8. Modification des CGU</h2>
          <p>L'éditeur se réserve le droit de modifier les présentes CGU à tout moment. Les utilisateurs seront informés des modifications substantielles. La poursuite de l'utilisation du Service après modification vaut acceptation des nouvelles CGU.</p>
        </section>

        <section>
          <h2 class="text-xl font-semibold text-white mb-3">9. Droit applicable</h2>
          <p>Les présentes CGU sont régies par le droit français. En cas de litige, les tribunaux compétents seront ceux du ressort du domicile de l'éditeur.</p>
        </section>

        <section>
          <h2 class="text-xl font-semibold text-white mb-3">10. Contact</h2>
          <p>Pour toute question relative aux présentes CGU : <a href="mailto:jean.fechter@gmail.com" class="text-indigo-400 hover:text-indigo-300">jean.fechter@gmail.com</a></p>
        </section>
      </div>
    </div>
  </div>
</template>
