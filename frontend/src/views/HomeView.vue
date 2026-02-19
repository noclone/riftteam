<template>
  <div class="bg-gray-900 text-white flex flex-col items-center justify-center p-8 flex-1">
    <h1 class="text-5xl font-bold mb-4">RiftTeam</h1>
    <p class="text-xl text-gray-400 mb-8 text-center max-w-lg">
      Un bot Discord pour rapidement trouver une équipe, des joueurs, ou un scrim.
    </p>
    <a
      href="https://discord.com/oauth2/authorize?client_id=1473337482375467193&scope=bot+applications.commands&permissions=18432"
      target="_blank"
      rel="noopener"
      class="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-3 px-8 rounded-lg text-lg transition"
    >
      Ajouter le bot à mon serveur
    </a>
    <RouterLink
      to="/create"
      class="mt-4 text-indigo-400 hover:text-indigo-300 transition"
    >
      Créer mon profil
    </RouterLink>
    <RouterLink to="/browse" class="mt-2 text-indigo-400 hover:text-indigo-300 transition">
      Parcourir les joueurs
    </RouterLink>
  </div>
</template>
