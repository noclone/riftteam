import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
    },
    {
      path: '/create',
      name: 'create',
      component: () => import('@/views/CreateProfileView.vue'),
    },
    {
      path: '/edit',
      name: 'edit',
      component: () => import('@/views/EditProfileView.vue'),
    },
    {
      path: '/p/:slug',
      name: 'profile',
      component: () => import('@/views/ProfileView.vue'),
    },
    {
      path: '/browse',
      name: 'browse',
      component: () => import('@/views/BrowseView.vue'),
    },
    {
      path: '/t/:slug',
      name: 'team',
      component: () => import('@/views/TeamView.vue'),
    },
    {
      path: '/team/create',
      name: 'team-create',
      component: () => import('@/views/CreateTeamView.vue'),
    },
    {
      path: '/team/edit',
      name: 'team-edit',
      component: () => import('@/views/EditTeamView.vue'),
    },
    {
      path: '/privacy',
      name: 'privacy',
      component: () => import('@/views/PrivacyView.vue'),
    },
    {
      path: '/legal',
      name: 'legal',
      component: () => import('@/views/LegalView.vue'),
    },
  ],
})

export default router
