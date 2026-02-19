<template>
  <div class="bg-gray-900 text-white flex flex-col items-center justify-center p-8 flex-1">
    <h1 class="text-5xl font-bold mb-4">RiftTeam</h1>
    <p class="text-xl text-gray-400 mb-8 text-center max-w-lg">
      Un bot Discord pour rapidement trouver une équipe, des joueurs, ou un scrim.
    </p>
    <RouterLink
      to="/create"
      class="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-3 px-8 rounded-lg text-lg transition"
    >
      Créer mon profil
    </RouterLink>
    <RouterLink to="/browse" class="mt-4 text-indigo-400 hover:text-indigo-300 transition">
      Parcourir les joueurs
    </RouterLink>
  </div>
</template>
