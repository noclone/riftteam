# RiftTeam — Architecture technique

---

## 1. Vue d'ensemble

```
┌─────────────────┐       ┌──────────────────────┐       ┌─────────────┐
│   Frontend       │       │   Backend API         │       │  Riot API   │
│   Vue 3 + Vite   │──────▶│   FastAPI (Python)    │──────▶│  (EUW)      │
│   (SPA)          │◀──────│                       │◀──────│             │
└─────────────────┘       └──────────────────────┘       └─────────────┘
                                    │
                           ┌────────┼────────┐
                           ▼        ▼        ▼
                    ┌──────────┐ ┌──────┐ ┌──────────────┐
                    │PostgreSQL│ │Pillow│ │ Discord Bot   │
                    │          │ │(OG)  │ │ (discord.py)  │
                    └──────────┘ └──────┘ └──────────────┘
```

Le bot Discord consomme l'API backend via HTTP. Il ne tape jamais directement l'API Riot ni la base de données.

Les actions de création/édition depuis le bot passent par un système de tokens : le bot génère un token temporaire (30 min) via l'API, puis redirige l'utilisateur vers le frontend avec ce token en query param.

---

## 2. Stack technique

| Composant | Techno |
|-----------|--------|
| Frontend | Vue 3.5 + Vite 6 + TypeScript + Vue Router + Pinia + Tailwind CSS 4 |
| Backend API | FastAPI 0.115 (Python 3.11+) |
| ORM | SQLAlchemy 2.0 (async) + Alembic 1.14 |
| BDD | PostgreSQL 15 (asyncpg) |
| Bot Discord | discord.py 2.4 + aiohttp |
| Image OG | Pillow 11 |
| Assets LoL | Data Dragon CDN |
| Code partagé | Package `shared/` importé par backend et bot |

---

## 3. Structure du projet

```
riftteam/
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── HomeView.vue
│   │   │   ├── CreateProfileView.vue
│   │   │   ├── EditProfileView.vue
│   │   │   ├── ProfileView.vue
│   │   │   ├── BrowseView.vue
│   │   │   ├── CreateTeamView.vue
│   │   │   ├── EditTeamView.vue
│   │   │   └── TeamView.vue
│   │   ├── api/
│   │   │   └── client.ts
│   │   ├── router/
│   │   │   └── index.ts
│   │   └── stores/
│   ├── package.json
│   └── vite.config.ts
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   ├── middleware/
│   │   │   └── rate_limit.py
│   │   ├── models/
│   │   │   ├── player.py
│   │   │   ├── champion.py
│   │   │   ├── team.py
│   │   │   ├── scrim.py
│   │   │   ├── snapshot.py
│   │   │   ├── action_token.py
│   │   │   └── guild_settings.py
│   │   ├── routers/
│   │   │   ├── players.py
│   │   │   ├── teams.py
│   │   │   ├── scrims.py
│   │   │   ├── riot.py
│   │   │   ├── og.py
│   │   │   ├── tokens.py
│   │   │   └── guild_settings.py
│   │   ├── schemas/
│   │   │   ├── player.py
│   │   │   ├── team.py
│   │   │   └── scrim.py
│   │   └── services/
│   │       ├── riot_api.py
│   │       ├── role_detector.py
│   │       ├── rank_utils.py
│   │       ├── player_helpers.py
│   │       ├── query_helpers.py
│   │       ├── og_generator.py
│   │       ├── snapshots.py
│   │       ├── sync.py
│   │       └── token_store.py
│   ├── alembic/
│   │   └── versions/             # 8 migrations
│   ├── tests/                    # 11 fichiers de tests
│   └── pyproject.toml
│
├── bot/
│   ├── bot.py
│   ├── config.py
│   ├── constants.py
│   ├── utils.py
│   ├── cogs/
│   │   ├── profile.py
│   │   ├── register.py
│   │   ├── edit.py
│   │   ├── lfp.py
│   │   ├── team.py
│   │   ├── matchmaking.py
│   │   ├── scrim.py
│   │   ├── reactivate.py
│   │   └── help.py
│   ├── tests/                    # 7 fichiers de tests
│   └── pyproject.toml
│
├── shared/
│   ├── riot_client.py
│   ├── constants.py
│   └── format.py
│
├── docker-compose.yml
├── .env.example
└── CLAUDE.md
```

---

## 4. Modèle de données

### `players`

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID PK | |
| riot_puuid | VARCHAR(78) UNIQUE | Identifiant Riot permanent |
| riot_game_name | VARCHAR(16) | |
| riot_tag_line | VARCHAR(5) | |
| region | VARCHAR(10) | Défaut `EUW1` |
| slug | VARCHAR(25) UNIQUE | `{game_name}-{tag_line}`, utilisé dans les URLs |
| rank_solo_tier | VARCHAR(15) | IRON → CHALLENGER |
| rank_solo_division | VARCHAR(5) | I → IV |
| rank_solo_lp | INTEGER | |
| rank_solo_wins | INTEGER | |
| rank_solo_losses | INTEGER | |
| rank_flex_tier | VARCHAR(15) | |
| rank_flex_division | VARCHAR(5) | |
| rank_flex_lp | INTEGER | |
| rank_flex_wins | INTEGER | |
| rank_flex_losses | INTEGER | |
| peak_solo_tier | VARCHAR(15) | Meilleur rang atteint (saison) |
| peak_solo_division | VARCHAR(5) | |
| peak_solo_lp | INTEGER | |
| primary_role | VARCHAR(10) | TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY |
| secondary_role | VARCHAR(10) | Si ≥ 20% des games |
| summoner_level | INTEGER | |
| profile_icon_id | INTEGER | |
| discord_user_id | VARCHAR(20) UNIQUE | `NULL` si profil créé uniquement via roster team |
| discord_username | VARCHAR(50) | |
| description | TEXT | |
| activities | VARCHAR[] | SCRIMS, TOURNOIS, LAN, FLEX, CLASH |
| ambiance | VARCHAR(10) | FUN, TRYHARD |
| frequency_min | INTEGER | Fréquence min par semaine |
| frequency_max | INTEGER | Fréquence max par semaine |
| is_lft | BOOLEAN | En recherche d'équipe |
| last_riot_sync | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

Index partiels : `idx_players_lft` (WHERE is_lft = TRUE), `idx_players_role`, `idx_players_rank`.

### `player_champions`

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID PK | |
| player_id | UUID FK → players | CASCADE |
| champion_id | INTEGER | ID Data Dragon |
| champion_name | VARCHAR(30) | |
| mastery_level | INTEGER | |
| mastery_points | INTEGER | |
| games_played | INTEGER | Sur les matchs récents de la saison |
| wins | INTEGER | |
| losses | INTEGER | |
| avg_kills | NUMERIC(4,1) | |
| avg_deaths | NUMERIC(4,1) | |
| avg_assists | NUMERIC(4,1) | |

Contrainte unique : `(player_id, champion_id)`.

### `teams`

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID PK | |
| name | VARCHAR(50) | |
| slug | VARCHAR(55) UNIQUE | |
| captain_discord_id | VARCHAR(20) UNIQUE | Un seul capitaine par équipe, une seule équipe par capitaine |
| captain_discord_name | VARCHAR(50) | |
| description | TEXT | |
| activities | VARCHAR[] | |
| ambiance | VARCHAR(10) | |
| frequency_min | INTEGER | |
| frequency_max | INTEGER | |
| wanted_roles | VARCHAR[] | Rôles recherchés |
| min_rank | VARCHAR(15) | Rang minimum accepté |
| max_rank | VARCHAR(15) | Rang maximum accepté |
| is_lfp | BOOLEAN | En recrutement |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

Index partiel : `idx_teams_lfp` (WHERE is_lfp = TRUE).

### `team_members`

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID PK | |
| team_id | UUID FK → teams | CASCADE |
| player_id | UUID FK → players UNIQUE | CASCADE, un joueur ne peut être que dans une seule équipe |
| role | VARCHAR(10) | TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY |

### `scrims`

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID PK | |
| team_id | UUID FK → teams | CASCADE |
| captain_discord_id | VARCHAR(20) | |
| min_rank | VARCHAR(15) | |
| max_rank | VARCHAR(15) | |
| scheduled_at | TIMESTAMPTZ | Date et heure du scrim |
| format | VARCHAR(10) | BO1, BO3, BO5 |
| game_count | INTEGER | Nombre de games (pour format custom type G3) |
| fearless | BOOLEAN | Mode fearless (draft sans champion en commun) |
| is_active | BOOLEAN | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

Index : `idx_scrims_active_scheduled` (is_active, scheduled_at). Un nouveau scrim désactive automatiquement les précédents de la même équipe.

### `rank_snapshots`

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID PK | |
| player_id | UUID FK → players | CASCADE |
| queue_type | VARCHAR(20) | RANKED_SOLO_5x5 ou RANKED_FLEX_SR |
| tier | VARCHAR(15) | |
| division | VARCHAR(5) | |
| lp | INTEGER | |
| wins | INTEGER | |
| losses | INTEGER | |
| recorded_at | TIMESTAMPTZ | |

Index : `idx_rank_snapshots_player_time` (player_id, recorded_at). Enregistré à chaque sync et chaque refresh.

### `champion_snapshots`

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID PK | |
| player_id | UUID FK → players | CASCADE |
| champions | JSONB | Snapshot complet des champions et stats |
| primary_role | VARCHAR(10) | |
| secondary_role | VARCHAR(10) | |
| recorded_at | TIMESTAMPTZ | |

Index : `idx_champion_snapshots_player_time` (player_id, recorded_at).

### `action_tokens`

| Colonne | Type | Description |
|---------|------|-------------|
| token | VARCHAR(32) PK | UUID hex |
| action | VARCHAR(20) | create, edit, team_create, team_edit |
| discord_user_id | VARCHAR(20) | |
| discord_username | VARCHAR(100) | |
| game_name | VARCHAR(50) | Optionnel selon l'action |
| tag_line | VARCHAR(10) | |
| slug | VARCHAR(100) | |
| team_name | VARCHAR(100) | |
| created_at | TIMESTAMPTZ | |

TTL de 30 minutes. Les tokens expirés sont nettoyés automatiquement. Les tokens `create` et `team_create` sont consommés (supprimés) à l'usage. Les tokens `edit` et `team_edit` sont réutilisables pendant leur durée de vie.

### `guild_settings`

| Colonne | Type | Description |
|---------|------|-------------|
| guild_id | VARCHAR(20) PK | Discord guild ID |
| announcement_channel_id | VARCHAR(20) | Channel pour les annonces automatiques |

---

## 5. Endpoints API

Base : `/api`

### Players

| Méthode | Route | Auth | Description |
|---------|-------|------|-------------|
| POST | `/players?token=` | Token (create) | Crée un profil. Fetch Riot API, enregistre snapshots, calcule peak rank |
| GET | `/players/{slug}` | — | Récupère un profil. Déclenche un lazy refresh si données > 6h |
| GET | `/players` | — | Liste avec filtres : `is_lft`, `role`, `min_rank`, `max_rank`, `limit`, `offset` |
| GET | `/players/by-discord/{discord_user_id}` | Bot secret | Lookup par Discord ID |
| PATCH | `/players/{slug}?token=` | Token (edit) | Met à jour les données déclaratives |
| DELETE | `/players/{slug}?token=` | Token (edit) | Supprime un profil |
| POST | `/players/{slug}/refresh` | Bot secret | Rafraîchit via Riot API (cooldown 1h) |
| POST | `/players/{slug}/reactivate` | Bot secret | Réactive un profil désactivé pour inactivité |

### Teams

| Méthode | Route | Auth | Description |
|---------|-------|------|-------------|
| POST | `/teams?token=` | Token (team_create) | Crée une équipe |
| GET | `/teams/{slug}` | — / Token | Publique si is_lfp=true, sinon nécessite token team_edit |
| GET | `/teams` | — | Liste avec filtres : `is_lfp`, `role`, `min_rank`, `max_rank`, `limit`, `offset` |
| GET | `/teams/by-captain/{discord_user_id}` | Bot secret | Lookup par capitaine |
| PATCH | `/teams/{slug}?token=` | Token (team_edit) | Met à jour |
| DELETE | `/teams/{slug}?token=` | Token (team_edit) | Supprime |
| POST | `/teams/{slug}/members` | Bot secret | Ajoute un joueur au roster (crée un profil léger si inexistant via Riot API) |
| DELETE | `/teams/{slug}/members/{player_slug}` | Bot secret | Retire un joueur du roster |
| POST | `/teams/{slug}/reactivate` | Bot secret | Réactive |

### Scrims

| Méthode | Route | Auth | Description |
|---------|-------|------|-------------|
| POST | `/scrims` | Bot secret | Crée un scrim (désactive les précédents de l'équipe) |
| GET | `/scrims` | — | Liste avec filtres : `min_rank`, `max_rank`, `scheduled_date`, `format`, `hour_min`, `hour_max` |
| DELETE | `/scrims/{scrim_id}` | Bot secret | Annule un scrim |
| DELETE | `/scrims/by-team/{team_slug}` | Bot secret | Annule tous les scrims actifs d'une équipe |

### Tokens

| Méthode | Route | Auth | Description |
|---------|-------|------|-------------|
| POST | `/tokens` | Bot secret | Génère un token d'action (retourne token + URL frontend) |
| GET | `/tokens/{token}/validate` | — | Valide un token et retourne ses métadonnées |

### Autres

| Méthode | Route | Auth | Description |
|---------|-------|------|-------------|
| GET | `/riot/check/{name}/{tag}` | — | Vérifie l'existence d'un Riot ID |
| GET | `/guild-settings/{guild_id}` | — | Paramètres d'un serveur Discord |
| PUT | `/guild-settings/{guild_id}` | Bot secret | Met à jour les paramètres |
| GET | `/health` | — | Health check (DB incluse) |
| POST | `/maintenance/deactivate-inactive` | Bot secret | Désactive les profils/teams inactifs > 14j |

### OpenGraph (hors préfixe `/api`)

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/p/{slug}` | Crawler → HTML avec meta tags OG. Navigateur → redirect vers la SPA |
| GET | `/t/{slug}` | Idem pour les équipes |
| GET | `/api/og/{slug}.png` | Image OG joueur (PNG 1200×630, cache mémoire 6h, max 500 entrées) |
| GET | `/api/og/team/{slug}.png` | Image OG équipe |

---

## 6. Commandes bot Discord

Toutes les commandes utilisent le préfixe `/rt-`. Le bot communique exclusivement avec l'API backend via HTTP (session `aiohttp` avec header `X-Bot-Secret`).

### Profil

| Commande | Cog | Description |
|----------|-----|-------------|
| `/rt-profil-create` | register | Génère un token create → envoie un lien vers le frontend |
| `/rt-profil-show <riot_id>` | profile | Affiche un embed riche du profil |
| `/rt-profil-edit` | edit | Génère un token edit → lien vers le frontend |
| `/rt-profil-post` | profile | Partage le profil dans le channel (non éphémère) |
| `/rt-profil-enable-lft` | reactivate | Réactive le statut LFT |

### Équipe

| Commande | Cog | Description |
|----------|-----|-------------|
| `/rt-team-create` | team | Génère un token team_create → lien vers le frontend |
| `/rt-team-edit` | team | Génère un token team_edit → lien vers le frontend |
| `/rt-team-roster add <riot_id> <role>` | team | Ajoute un joueur au roster |
| `/rt-team-roster remove <riot_id>` | team | Retire un joueur |
| `/rt-team-post` | team | Partage l'équipe dans le channel |
| `/rt-team-enable-lfp` | reactivate | Réactive le statut LFP |

### Recherche

| Commande | Cog | Description |
|----------|-----|-------------|
| `/rt-lfp [role] [min_rank] [max_rank]` | lfp | Liste paginée des joueurs LFT avec boutons de contact |
| `/rt-lft [role] [min_rank] [max_rank]` | matchmaking | Liste paginée des équipes LFP |
| `/rt-apply <team>` | matchmaking | Postule à une équipe (DM au capitaine) |
| `/rt-recruit <riot_id>` | matchmaking | Recrute un joueur (DM au joueur) |

### Scrims

| Commande | Cog | Description |
|----------|-----|-------------|
| `/rt-scrim-post` | scrim | Publie un scrim (date, heure, format, rang, fearless) |
| `/rt-scrim-search [date] [min_rank] [max_rank] [format] [hour_min] [hour_max]` | scrim | Recherche paginée de scrims |
| `/rt-scrim-cancel` | scrim | Annule les scrims actifs de l'équipe |

### Autre

| Commande | Cog | Description |
|----------|-----|-------------|
| `/rt-help` | help | Liste toutes les commandes |

---

## 7. Frontend — Routes

| Route | Vue | Description |
|-------|-----|-------------|
| `/` | HomeView | Landing page |
| `/create?token=` | CreateProfileView | Formulaire de création de profil |
| `/edit?token=` | EditProfileView | Formulaire d'édition de profil |
| `/p/:slug` | ProfileView | Page profil publique |
| `/browse` | BrowseView | Recherche/filtre de joueurs LFT |
| `/t/:slug` | TeamView | Page équipe publique |
| `/team/create?token=` | CreateTeamView | Formulaire de création d'équipe |
| `/team/edit?token=` | EditTeamView | Formulaire d'édition d'équipe |

Les formulaires de création/édition nécessitent un token valide passé en query param, généré par le bot Discord.

---

## 8. Intégration Riot API

### Client (`shared/riot_client.py`)

Singleton `RiotClient` injecté via `app.state` au démarrage de FastAPI.

**Rate limiting côté client** :
- Fenêtre courte : 18 req/s (marge sur la limite de 20/s)
- Fenêtre longue : 95 req/2min (marge sur la limite de 100/2min)
- Verrou asyncio pour garantir l'atomicité du décompte
- Retry automatique sur 429 (Retry-After header) et sur 5xx (backoff exponentiel, 3 tentatives)

**Cache mémoire** : TTL 5 min, max 1000 entrées. Évite les appels redondants pendant une même session de sync.

### Endpoints Riot utilisés

| Endpoint | Données |
|----------|---------|
| `GET /riot/account/v1/accounts/by-riot-id/{name}/{tag}` | PUUID, gameName, tagLine |
| `GET /lol/summoner/v4/summoners/by-puuid/{puuid}` | Niveau, icône |
| `GET /lol/league/v4/entries/by-puuid/{puuid}` | Rang solo/flex (tier, division, LP, W/L) |
| `GET /lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/top?count=10` | Top 10 masteries |
| `GET /lol/match/v5/matches/by-puuid/{puuid}/ids?queue=&count=&startTime=` | IDs des matchs |
| `GET /lol/match/v5/matches/{matchId}` | Détails match (rôle, champion, KDA, résultat) |

Régions : `europe.api.riotgames.com` pour account et match, `euw1.api.riotgames.com` pour summoner, league et mastery.

### Détection du rôle principal

1. Fetch les IDs de matchs de la saison en cours, par priorité de queue :
   - Ranked Solo (420) — jusqu'à 100 matchs
   - Si < 10 matchs : compléter avec Ranked Flex (440)
   - Si < 10 : compléter avec Normal Draft (400)
2. Fetch le détail des 50 premiers matchs (cap `MATCH_FETCH_LIMIT`)
3. Comptage des rôles (`teamPosition`) et agrégation des stats par champion
4. Rôle principal = le plus joué. Rôle secondaire = le 2ème si ≥ 20% des games.

---

## 9. Synchronisation et tâches de fond

### Sync des rangs (backend — boucle dans `lifespan`)

- **Intervalle** : 12 heures
- **Cible** : tous les joueurs avec `is_lft = True`
- **Données** : rang solo/flex, summoner level
- **Actions** : mise à jour player, enregistrement `rank_snapshot`, mise à jour `peak_rank`
- **Coût** : 2 appels Riot API par profil

### Lazy refresh (backend — `BackgroundTasks`)

- Déclenché à chaque `GET /players/{slug}` si `last_riot_sync > 6h`
- Même logique que la sync mais pour un seul joueur
- Garde un `set` en mémoire pour éviter les doublons

### Refresh manuel (`POST /players/{slug}/refresh`)

- Déclenché par le bot
- Cooldown 1 heure
- Full refresh : rang, champions, match history, snapshots

### Désactivation des inactifs (bot → backend)

- Le bot appelle `POST /maintenance/deactivate-inactive` toutes les 12 heures
- Désactive les joueurs LFT et équipes LFP dont `updated_at > 14 jours`
- Retourne la liste des `discord_user_id` désactivés
- Le bot envoie un DM à chaque utilisateur avec un bouton "Réactiver"

---

## 10. Authentification et sécurité

### Token d'action (bot → frontend)

Le bot est le seul point d'entrée pour créer/modifier du contenu. Le flow :

1. L'utilisateur tape une commande Discord (ex: `/rt-profil-create`)
2. Le bot appelle `POST /api/tokens` avec `X-Bot-Secret` → reçoit un token + URL
3. Le bot envoie un lien vers le frontend avec `?token=...`
4. Le frontend valide le token via `GET /api/tokens/{token}/validate`
5. Le frontend soumet le formulaire avec `?token=` en query param
6. Le backend consomme le token et exécute l'action

Types : `create` (profil), `edit` (profil), `team_create`, `team_edit`.

### Bot secret (`X-Bot-Secret` header)

Header partagé entre le bot et le backend. Protège les endpoints sensibles :
- Création/validation de tokens
- Refresh de profil
- Gestion du roster
- Gestion des scrims
- Désactivation des inactifs
- Guild settings

### Rate limiting

Middleware custom sur les routes `GET /api/*` :
- 60 requêtes par IP par minute
- Basé sur `X-Forwarded-For` (reverse proxy) ou `request.client.host`
- Nettoyage périodique des buckets (toutes les 5 min, max 10 000 entrées)

---

## 11. OpenGraph et embeds Discord

### Mécanisme

Quand un lien `riftteam.fr/p/{slug}` est posté dans Discord :

1. Le crawler Discord (`Discordbot` user-agent) fetch l'URL
2. `og.py` détecte le crawler et retourne un HTML minimal avec meta tags OG
3. Discord affiche un embed riche avec titre, description, image et `theme-color`

Pour les navigateurs : redirect 302 vers la SPA Vue.

### Meta tags générés

- `og:title` : `{RiotID} — {Rank} {Role}`
- `og:description` : `{WR} · {Champions} · {Activities}`
- `og:image` : URL vers `/api/og/{slug}.png`
- `theme-color` : couleur hex du rang (Iron=gris → Challenger=doré)

### Image OG (Pillow)

Card PNG 1200×630 générée dynamiquement. Cache mémoire : TTL 6h, max 500 entrées. Invalidé lors d'un refresh de profil. Deux variantes : joueur et équipe.

---

## 12. Configuration

Variables d'environnement (`.env`) :

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | URL PostgreSQL (asyncpg) |
| `RIOT_API_KEY` | Clé API Riot Games |
| `APP_URL` | URL du frontend (CORS, redirections) |
| `API_URL` | URL du backend (meta tags OG) |
| `SECRET_KEY` | Clé secrète backend |
| `BOT_API_SECRET` | Secret partagé bot ↔ backend |
| `DISCORD_BOT_TOKEN` | Token du bot Discord |
| `DEV_GUILD_ID` | Optionnel : sync les commandes sur un seul serveur en dev |
