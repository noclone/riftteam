import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior() {
    return { top: 0 }
  },
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
    {
      path: '/terms',
      name: 'terms',
      component: () => import('@/views/TermsView.vue'),
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
    },
  ],
})

export default router
