# RiftTeam — Architecture & Feature Spec V1

> Plateforme de profils joueurs LoL pour la recherche d'équipe amateur
> Focus communauté francophone EUW

---

## 1. Vision Produit

### Le problème
Un joueur LoL amateur qui cherche une équipe (ou une équipe qui cherche un joueur) doit aujourd'hui poster un message texte libre dans un channel Discord, sans vérification, sans standardisation, et sans suivi. Le message est enterré en quelques heures. Les alternatives comme Hextech Tools LFT Image Maker génèrent des images statiques non vérifiées qui deviennent obsolètes immédiatement.

### La solution V1
Un profil joueur **alimenté par l'API Riot**, créé en 60 secondes, partageable dans Discord via un **lien avec embed riche** ou via un **bot Discord**, et toujours à jour automatiquement.

### Ce que V1 n'est PAS
- Pas un outil de matchmaking automatique (V2+)
- Pas un scrim scheduler (V3+)
- Pas un système de réputation (V2+)
- Pas un concurrent de Discord pour la communication

---

## 2. User Stories V1

### Joueur LFT (Looking For Team)
1. Je vais sur `riftteam.gg`, j'entre mon Riot ID (`Pseudo#TAG`)
2. Le site récupère automatiquement : mon rang, mes top champions, mon rôle principal, mon winrate
3. Je complète : mes disponibilités, ce que je cherche, mon Discord, une description libre
4. J'obtiens un lien `https://riftteam.gg/p/Pseudo-TAG`
5. Je colle ce lien dans un channel Discord → Discord affiche un embed propre avec mon rang, mon rôle, mes top champs
6. Les teams intéressées consultent mon profil complet via le lien et me contactent sur Discord

### Capitaine d'équipe LFP (Looking For Player)
1. Il voit un embed dans un channel Discord → clique sur le lien
2. Il arrive sur le profil complet du joueur : stats vérifiées, champions, historique, dispo
3. Il évalue le joueur sur des données réelles tirées de l'API Riot
4. Il contacte le joueur via le Discord affiché

### Admin de serveur Discord
1. Il installe le bot RiftTeam sur son serveur
2. Ses membres peuvent taper `/profil Pseudo#TAG` pour afficher un embed
3. Le channel LFT/LFP est plus propre : les embeds sont standardisés
4. Il peut configurer un channel dédié où le bot poste les nouveaux profils

---

## 3. Architecture Technique

### Vue d'ensemble

```
┌─────────────────┐       ┌──────────────────┐       ┌─────────────┐
│   Frontend       │       │   Backend API     │       │  Riot API   │
│   Vue 3 + Vite   │──────▶│   FastAPI (Python) │──────▶│  (EUW)      │
│   (SPA)          │◀──────│                    │◀──────│             │
└─────────────────┘       └──────────────────┘       └─────────────┘
                                   │
                          ┌────────┼────────┐
                          ▼        ▼        ▼
                   ┌──────────┐ ┌──────┐ ┌──────────────┐
                   │PostgreSQL│ │Pillow│ │ Discord Bot   │
                   │          │ │(OG)  │ │ (discord.py)  │
                   └──────────┘ └──────┘ └──────────────┘
```

### Stack Technique

| Composant | Techno | Justification |
|-----------|--------|---------------|
| Frontend | **Vue 3 + Vite + Vue Router + Pinia** | SPA classique, rapide, stack maîtrisée |
| UI | **Tailwind CSS** | Utility-first, rapide à prototyper, bon écosystème |
| Backend API | **FastAPI (Python 3.11+)** | Async natif, typing, Swagger auto, sert aussi les meta tags OG |
| ORM | **SQLAlchemy 2.0** + **Alembic** (migrations) | Mature, bien documenté, async supporté |
| Bot Discord | **discord.py 2.x** | Même langage que le backend, partage les modèles et la logique |
| OG Image | **Pillow** (Python) | Génération de cards PNG côté serveur |
| BDD | **PostgreSQL 15+** | Relationnel, robuste, JSONB pour les données flexibles |
| Cache | **Cache mémoire** (V1) → **Redis** (V2+) | Pour les données Riot API et le rate limiting |
| Assets LoL | **Data Dragon CDN** | `https://ddragon.leagueoflegends.com/cdn/` |
| Hébergement | **VPS** (Hetzner/OVH) ou **Railway** | Tout sur une machine : API, bot, cron jobs |

### Structure du projet

```
riftteam/
├── frontend/                  # Vue 3 SPA
│   ├── src/
│   │   ├── views/
│   │   │   ├── Home.vue            # Page d'accueil
│   │   │   ├── CreateProfile.vue   # Formulaire de création
│   │   │   ├── Profile.vue         # Page profil publique
│   │   │   └── Browse.vue          # Liste des joueurs LFT
│   │   ├── components/
│   │   ├── stores/             # Pinia stores
│   │   ├── api/                # Client API (axios/fetch)
│   │   └── router/
│   ├── package.json
│   └── vite.config.js
│
├── backend/                   # FastAPI
│   ├── app/
│   │   ├── main.py                 # App FastAPI + route OG
│   │   ├── config.py               # Settings & env vars
│   │   ├── models/                 # SQLAlchemy models
│   │   │   ├── player.py
│   │   │   └── champion.py
│   │   ├── routers/
│   │   │   ├── players.py          # CRUD profils
│   │   │   ├── riot.py             # Proxy vers Riot API
│   │   │   └── og.py               # Génération OG image
│   │   ├── services/
│   │   │   ├── riot_api.py         # Client Riot API + rate limiting
│   │   │   ├── role_detector.py    # Calcul du rôle principal
│   │   │   ├── og_generator.py     # Génération card PNG (Pillow)
│   │   │   └── sync.py             # Cron de sync des données
│   │   └── utils/
│   ├── alembic/                # Migrations DB
│   ├── requirements.txt
│   └── Dockerfile
│
├── bot/                       # Discord Bot
│   ├── bot.py                      # Main bot
│   ├── cogs/
│   │   ├── profile.py              # /profil command
│   │   ├── lft.py                  # /lft command
│   │   └── admin.py                # /setup command
│   └── requirements.txt
│
├── shared/                    # Code partagé backend + bot
│   ├── riot_client.py              # Client Riot API réutilisable
│   ├── models.py                   # Modèles de données partagés
│   └── constants.py                # Rangs, rôles, couleurs, etc.
│
├── docker-compose.yml
└── README.md
```

---

## 4. Modèle de Données

### Table `players`
```sql
CREATE TABLE players (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Identité Riot
  riot_puuid      VARCHAR(78) UNIQUE NOT NULL,
  riot_game_name  VARCHAR(16) NOT NULL,
  riot_tag_line   VARCHAR(5) NOT NULL,
  region          VARCHAR(10) DEFAULT 'EUW1',
  
  -- Données Riot (auto-fetched via API)
  rank_solo_tier      VARCHAR(15),     -- IRON, BRONZE, SILVER, GOLD, PLATINUM, EMERALD, DIAMOND, MASTER, GRANDMASTER, CHALLENGER
  rank_solo_division  VARCHAR(5),      -- I, II, III, IV
  rank_solo_lp        INTEGER,
  rank_solo_wins      INTEGER,
  rank_solo_losses    INTEGER,
  rank_flex_tier      VARCHAR(15),
  rank_flex_division  VARCHAR(5),
  primary_role        VARCHAR(10),     -- TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY
  secondary_role      VARCHAR(10),
  summoner_level      INTEGER,
  profile_icon_id     INTEGER,
  
  -- Données déclaratives (saisies par le joueur)
  discord_username    VARCHAR(50),
  description         TEXT,
  looking_for         VARCHAR(20),     -- TEAM, DUO, CLASH, SCRIM, ANY
  ambition            VARCHAR(20),     -- CHILL, IMPROVE, COMPETITIVE, TRYHARD
  languages           TEXT[] DEFAULT ARRAY['fr'],
  
  -- Disponibilités
  availability        JSONB,
  -- Format: {"lundi": ["soir"], "mercredi": ["soir"], "samedi": ["aprem", "soir"], "dimanche": ["aprem", "soir"]}
  
  -- État
  is_lft              BOOLEAN DEFAULT TRUE,     -- actuellement en recherche
  last_riot_sync      TIMESTAMPTZ,
  created_at          TIMESTAMPTZ DEFAULT NOW(),
  updated_at          TIMESTAMPTZ DEFAULT NOW(),
  
  -- Slug pour l'URL
  slug                VARCHAR(25) GENERATED ALWAYS AS (riot_game_name || '-' || riot_tag_line) STORED UNIQUE
);

CREATE INDEX idx_players_lft ON players (is_lft) WHERE is_lft = TRUE;
CREATE INDEX idx_players_role ON players (primary_role);
CREATE INDEX idx_players_rank ON players (rank_solo_tier);
```

### Table `player_champions`
```sql
CREATE TABLE player_champions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  player_id       UUID REFERENCES players(id) ON DELETE CASCADE,
  champion_id     INTEGER NOT NULL,
  champion_name   VARCHAR(30) NOT NULL,
  
  -- Données de mastery (champion-mastery-v4)
  mastery_level   INTEGER,
  mastery_points  INTEGER,
  
  -- Données calculées depuis le match history
  games_played    INTEGER DEFAULT 0,     -- sur les 20 derniers ranked
  wins            INTEGER DEFAULT 0,
  losses          INTEGER DEFAULT 0,
  avg_kills       DECIMAL(4,1),
  avg_deaths      DECIMAL(4,1),
  avg_assists     DECIMAL(4,1),
  
  UNIQUE(player_id, champion_id)
);

CREATE INDEX idx_champions_player ON player_champions (player_id);
```

---

## 5. API Riot — Intégration

### Endpoints utilisés

| Endpoint | Données récupérées | Quand |
|----------|-------------------|-------|
| `GET /riot/account/v1/accounts/by-riot-id/{name}/{tag}` | PUUID | Création de profil |
| `GET /lol/summoner/v4/summoners/by-puuid/{puuid}` | Niveau, icône | Création + sync |
| `GET /lol/league/v4/entries/by-summoner/{summonerId}` | Rang solo/flex, wins, losses | Création + sync |
| `GET /lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/top?count=10` | Top 10 champions mastery | Création + sync |
| `GET /lol/match/v5/matches/by-puuid/{puuid}/ids?queue=420&count=20` | IDs des 20 derniers matchs ranked solo | Création + sync |
| `GET /lol/match/v5/matches/{matchId}` | Détails du match (rôle, champion, KDA) | Création + sync |

### Calcul du rôle principal

```python
# services/role_detector.py

async def detect_roles(puuid: str, riot_client: RiotClient) -> tuple[str, str | None]:
    """
    Détermine le rôle principal et secondaire d'un joueur
    à partir de ses matchs récents.
    
    Priorité des queues :
    1. Ranked Solo/Duo (queue=420) — 20 derniers matchs
    2. Si < 10 matchs solo : compléter avec Ranked Flex (queue=440)
    3. Si toujours < 10 : compléter avec Normal Draft (queue=400)
    """
    
    MINIMUM_GAMES = 10
    
    # 1. Fetch ranked solo en priorité
    match_ids = await riot_client.get_match_ids(puuid, queue=420, count=20)
    
    # 2. Compléter avec flex si pas assez
    if len(match_ids) < MINIMUM_GAMES:
        flex_ids = await riot_client.get_match_ids(puuid, queue=440, count=20 - len(match_ids))
        match_ids.extend(flex_ids)
    
    # 3. Compléter avec normales si toujours pas assez
    if len(match_ids) < MINIMUM_GAMES:
        normal_ids = await riot_client.get_match_ids(puuid, queue=400, count=20 - len(match_ids))
        match_ids.extend(normal_ids)
    
    # 4. Fetch les détails de chaque match et extraire le rôle
    role_counts = {"TOP": 0, "JUNGLE": 0, "MIDDLE": 0, "BOTTOM": 0, "UTILITY": 0}
    champion_stats = {}  # champion_name -> {games, wins, kills, deaths, assists}
    
    for match_id in match_ids:
        match = await riot_client.get_match(match_id)
        participant = find_participant(match, puuid)
        
        if participant:
            role = participant["teamPosition"]
            if role in role_counts:
                role_counts[role] += 1
            
            # Collecter les stats par champion en même temps
            champ = participant["championName"]
            if champ not in champion_stats:
                champion_stats[champ] = {"games": 0, "wins": 0, "kills": 0, "deaths": 0, "assists": 0}
            champion_stats[champ]["games"] += 1
            champion_stats[champ]["wins"] += 1 if participant["win"] else 0
            champion_stats[champ]["kills"] += participant["kills"]
            champion_stats[champ]["deaths"] += participant["deaths"]
            champion_stats[champ]["assists"] += participant["assists"]
    
    # 5. Déterminer les rôles
    sorted_roles = sorted(role_counts.items(), key=lambda x: x[1], reverse=True)
    primary_role = sorted_roles[0][0] if sorted_roles[0][1] > 0 else None
    
    total_games = sum(role_counts.values())
    secondary_role = None
    if total_games > 0 and sorted_roles[1][1] / total_games >= 0.20:  # Au moins 20% des games
        secondary_role = sorted_roles[1][0]
    
    return primary_role, secondary_role, champion_stats


def find_participant(match_data: dict, puuid: str) -> dict | None:
    """Trouve les données du joueur dans un match."""
    for participant in match_data["info"]["participants"]:
        if participant["puuid"] == puuid:
            return participant
    return None
```

### Rate Limiting côté client

```python
# shared/riot_client.py

import asyncio
import time
from collections import deque

class RiotClient:
    """
    Client Riot API avec rate limiting intégré.
    
    Limites clé de dev : 20 req/s, 100 req/2min
    Limites clé prod :  variable, typiquement plus élevé
    """
    
    def __init__(self, api_key: str, requests_per_second: int = 18, requests_per_2min: int = 95):
        self.api_key = api_key
        self.base_url = "https://europe.api.riotgames.com"
        self.euw_url = "https://euw1.api.riotgames.com"
        self.short_window = deque()   # timestamps des requêtes (1s)
        self.long_window = deque()    # timestamps des requêtes (2min)
        self.rps = requests_per_second
        self.rpm = requests_per_2min
    
    async def _wait_for_rate_limit(self):
        """Attend si nécessaire pour respecter les rate limits."""
        now = time.time()
        
        # Nettoyer les vieilles entrées
        while self.short_window and now - self.short_window[0] > 1:
            self.short_window.popleft()
        while self.long_window and now - self.long_window[0] > 120:
            self.long_window.popleft()
        
        # Attendre si on dépasse les limites
        if len(self.short_window) >= self.rps:
            wait = 1 - (now - self.short_window[0])
            if wait > 0:
                await asyncio.sleep(wait)
        
        if len(self.long_window) >= self.rpm:
            wait = 120 - (now - self.long_window[0])
            if wait > 0:
                await asyncio.sleep(wait)
        
        now = time.time()
        self.short_window.append(now)
        self.long_window.append(now)
    
    async def _request(self, url: str) -> dict:
        await self._wait_for_rate_limit()
        async with aiohttp.ClientSession() as session:
            headers = {"X-Riot-Token": self.api_key}
            async with session.get(url, headers=headers) as resp:
                if resp.status == 429:
                    retry_after = int(resp.headers.get("Retry-After", 5))
                    await asyncio.sleep(retry_after)
                    return await self._request(url)  # Retry
                resp.raise_for_status()
                return await resp.json()
    
    async def get_account_by_riot_id(self, game_name: str, tag_line: str) -> dict:
        url = f"{self.base_url}/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        return await self._request(url)
    
    async def get_summoner_by_puuid(self, puuid: str) -> dict:
        url = f"{self.euw_url}/lol/summoner/v4/summoners/by-puuid/{puuid}"
        return await self._request(url)
    
    async def get_league_entries(self, summoner_id: str) -> list:
        url = f"{self.euw_url}/lol/league/v4/entries/by-summoner/{summoner_id}"
        return await self._request(url)
    
    async def get_top_masteries(self, puuid: str, count: int = 10) -> list:
        url = f"{self.euw_url}/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/top?count={count}"
        return await self._request(url)
    
    async def get_match_ids(self, puuid: str, queue: int = 420, count: int = 20) -> list:
        url = f"{self.base_url}/lol/match/v5/matches/by-puuid/{puuid}/ids?queue={queue}&count={count}"
        return await self._request(url)
    
    async def get_match(self, match_id: str) -> dict:
        url = f"{self.base_url}/lol/match/v5/matches/{match_id}"
        return await self._request(url)
```

### Stratégie de synchronisation

| Déclencheur | Données rafraîchies | Coût API | Fréquence max |
|-------------|---------------------|----------|---------------|
| Création de profil | Tout (rang, masteries, match history) | ~25 appels | 1 fois |
| Bouton "Rafraîchir" sur le profil | Tout | ~25 appels | 1x par heure (cooldown) |
| Cron job | Rang uniquement (profils actifs) | 2 appels/profil | Toutes les 12h |
| Consultation profil (si données > 6h) | Rang uniquement | 2 appels | Lazy, à la volée |

Budget estimé pour 1000 profils actifs :
- Cron : 1000 × 2 appels × 2/jour = **4 000 appels/jour**
- Consultations lazy : ~500/jour × 2 appels = **1 000 appels/jour**
- Rafraîchissements manuels : ~100/jour × 25 appels = **2 500 appels/jour**
- **Total : ~7 500 appels/jour** → très confortable en clé Production

---

## 6. Embeds Discord — Deux Mécanismes

### A. Embed via lien (OpenGraph)

Quand quelqu'un colle `https://riftteam.gg/p/Pseudo-TAG` dans Discord, le crawler Discord (`Discordbot` user-agent) fetch l'URL. FastAPI détecte le crawler et lui sert un HTML minimal avec les meta tags.

```python
# routers/og.py

from fastapi import Request
from fastapi.responses import HTMLResponse, FileResponse

CRAWLER_BOTS = ["discordbot", "twitterbot", "facebookexternalhit", "telegrambot", "slackbot"]

@app.get("/p/{slug}")
async def player_page(request: Request, slug: str):
    ua = request.headers.get("user-agent", "").lower()
    is_crawler = any(bot in ua for bot in CRAWLER_BOTS)
    
    if is_crawler:
        player = await get_player_by_slug(slug)
        if not player:
            return HTMLResponse("<html><head><title>Joueur non trouvé</title></head></html>", status_code=404)
        
        rank = format_rank(player)        # "Emerald 2 — 58% WR"
        role = format_role(player)        # "🎯 Jungle"
        champs = format_champions(player) # "Lee Sin · Vi · Viego"
        color = rank_to_hex_color(player) # "#50C878" (vert pour Emerald)
        og_image = f"https://riftteam.gg/api/og/{slug}.png"
        
        html = f"""<!DOCTYPE html>
        <html>
        <head>
            <meta property="og:site_name" content="RiftTeam" />
            <meta property="og:title" content="{player.riot_game_name}#{player.riot_tag_line} — {rank}" />
            <meta property="og:description" content="{role} · {champs} · {player.looking_for_label}" />
            <meta property="og:image" content="{og_image}" />
            <meta property="og:image:width" content="1200" />
            <meta property="og:image:height" content="630" />
            <meta property="og:url" content="https://riftteam.gg/p/{slug}" />
            <meta property="og:type" content="profile" />
            <meta name="theme-color" content="{color}" />
        </head>
        <body></body>
        </html>"""
        return HTMLResponse(html)
    
    # Navigateur normal → servir la SPA Vue
    return FileResponse("frontend/dist/index.html")
```

### B. Embed via bot Discord

```python
# bot/cogs/profile.py

import discord
from discord import app_commands
from discord.ext import commands

RANK_COLORS = {
    "IRON": 0x6B6B6B, "BRONZE": 0x8B4513, "SILVER": 0xC0C0C0,
    "GOLD": 0xFFD700, "PLATINUM": 0x00CED1, "EMERALD": 0x50C878,
    "DIAMOND": 0x4169E1, "MASTER": 0x9B30FF, "GRANDMASTER": 0xDC143C,
    "CHALLENGER": 0xF0E68C,
}

ROLE_EMOJIS = {
    "TOP": "🛡️", "JUNGLE": "🌿", "MIDDLE": "🔥", "BOTTOM": "🏹", "UTILITY": "💫"
}

class ProfileCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_base = "https://riftteam.gg/api"
    
    @app_commands.command(name="profil", description="Afficher le profil RiftTeam d'un joueur")
    @app_commands.describe(riot_id="Riot ID du joueur (ex: Pseudo#TAG)")
    async def profil(self, interaction: discord.Interaction, riot_id: str):
        await interaction.response.defer()
        
        # Parse le Riot ID
        if "#" not in riot_id:
            await interaction.followup.send("❌ Format invalide. Utilise `Pseudo#TAG`.", ephemeral=True)
            return
        
        name, tag = riot_id.rsplit("#", 1)
        slug = f"{name}-{tag}"
        
        # Fetch le profil depuis l'API backend
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_base}/players/{slug}") as resp:
                if resp.status == 404:
                    await interaction.followup.send(
                        f"❌ Aucun profil RiftTeam trouvé pour `{riot_id}`.\n"
                        f"👉 Crée ton profil sur https://riftteam.gg",
                        ephemeral=True
                    )
                    return
                player = await resp.json()
        
        # Construire l'embed
        rank_tier = player.get("rank_solo_tier", "UNRANKED")
        color = RANK_COLORS.get(rank_tier, 0x808080)
        
        rank_display = format_rank_display(player)
        role_emoji = ROLE_EMOJIS.get(player.get("primary_role", ""), "❓")
        role_name = translate_role(player.get("primary_role"))
        
        # Top 3 champions
        champions = player.get("top_champions", [])[:3]
        champ_display = " · ".join([f"**{c['name']}** ({c['win_rate']}%)" for c in champions]) or "Aucune donnée"
        
        # Disponibilités
        availability = format_availability(player.get("availability", {}))
        
        embed = discord.Embed(
            title=f"{player['riot_game_name']}#{player['riot_tag_line']}",
            url=f"https://riftteam.gg/p/{slug}",
            color=color
        )
        
        embed.add_field(name="Rang", value=rank_display, inline=True)
        embed.add_field(name="Rôle", value=f"{role_emoji} {role_name}", inline=True)
        embed.add_field(name="Cherche", value=player.get("looking_for_label", "—"), inline=True)
        embed.add_field(name="Champions", value=champ_display, inline=False)
        
        if availability:
            embed.add_field(name="Disponibilités", value=availability, inline=False)
        
        if player.get("description"):
            desc = player["description"][:150]
            if len(player["description"]) > 150:
                desc += "..."
            embed.add_field(name="Description", value=desc, inline=False)
        
        # Thumbnail : icône de rang
        rank_icon_url = get_rank_icon_url(rank_tier)
        if rank_icon_url:
            embed.set_thumbnail(url=rank_icon_url)
        
        embed.set_footer(text=f"RiftTeam · Mis à jour {format_relative_time(player['last_riot_sync'])}")
        
        await interaction.followup.send(embed=embed)
```

---

## 7. Génération de l'Image OG (Card de Profil)

### Endpoint : `GET /api/og/{slug}.png`

FastAPI génère une image PNG 1200×630px avec Pillow.

```python
# services/og_generator.py

from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import aiohttp

# Pré-charger les fonts et assets
FONT_TITLE = ImageFont.truetype("assets/fonts/Inter-Bold.ttf", 48)
FONT_RANK = ImageFont.truetype("assets/fonts/Inter-SemiBold.ttf", 36)
FONT_BODY = ImageFont.truetype("assets/fonts/Inter-Regular.ttf", 28)
FONT_SMALL = ImageFont.truetype("assets/fonts/Inter-Regular.ttf", 22)

# Couleurs de fond par rang
RANK_GRADIENTS = {
    "IRON":        ((60, 60, 60), (40, 40, 40)),
    "BRONZE":      ((80, 50, 20), (50, 30, 10)),
    "SILVER":      ((140, 150, 160), (100, 110, 120)),
    "GOLD":        ((160, 130, 40), (120, 95, 20)),
    "PLATINUM":    ((20, 120, 130), (10, 80, 90)),
    "EMERALD":     ((30, 130, 80), (15, 90, 55)),
    "DIAMOND":     ((40, 70, 160), (20, 40, 120)),
    "MASTER":      ((100, 30, 160), (70, 15, 120)),
    "GRANDMASTER": ((170, 30, 50), (120, 15, 30)),
    "CHALLENGER":  ((180, 160, 50), (140, 120, 30)),
}

async def generate_og_card(player: dict) -> bytes:
    """Génère une card PNG 1200x630 pour un joueur."""
    
    rank_tier = player.get("rank_solo_tier", "UNRANKED")
    colors = RANK_GRADIENTS.get(rank_tier, ((50, 50, 50), (30, 30, 30)))
    
    # Créer l'image de base
    img = Image.new("RGB", (1200, 630), colors[0])
    draw = ImageDraw.Draw(img)
    
    # Pseudo#TAG
    riot_id = f"{player['riot_game_name']}#{player['riot_tag_line']}"
    draw.text((60, 40), riot_id, font=FONT_TITLE, fill="white")
    
    # Rang
    rank_text = format_rank(player)  # "Emerald 2 — 58% WR — 245W/178L"
    draw.text((60, 110), rank_text, font=FONT_RANK, fill=(255, 255, 255, 200))
    
    # Rôle
    role_text = f"Main {translate_role(player.get('primary_role', ''))}"
    draw.text((60, 170), role_text, font=FONT_BODY, fill=(255, 255, 255, 180))
    
    # Champions (icônes + noms)
    y_champs = 240
    x = 60
    for i, champ in enumerate(player.get("top_champions", [])[:4]):
        # Charger l'icône du champion depuis Data Dragon (cache local)
        icon = await load_champion_icon(champ["name"])
        if icon:
            icon = icon.resize((64, 64))
            img.paste(icon, (x, y_champs))
        
        draw.text((x, y_champs + 70), champ["name"], font=FONT_SMALL, fill="white")
        wr_text = f"{champ['win_rate']}% WR"
        draw.text((x, y_champs + 95), wr_text, font=FONT_SMALL, fill=(200, 200, 200))
        x += 150
    
    # Ce que le joueur cherche
    if player.get("looking_for_label"):
        draw.text((60, 420), f"🔍 {player['looking_for_label']}", font=FONT_BODY, fill="white")
    
    # Disponibilités
    if player.get("availability_summary"):
        draw.text((60, 470), f"📅 {player['availability_summary']}", font=FONT_BODY, fill=(200, 200, 200))
    
    # Logo RiftTeam en bas à droite
    draw.text((1000, 580), "riftteam.gg", font=FONT_SMALL, fill=(150, 150, 150))
    
    # Icône de rang en haut à droite
    rank_icon = await load_rank_icon(rank_tier)
    if rank_icon:
        rank_icon = rank_icon.resize((120, 120))
        img.paste(rank_icon, (1040, 30), rank_icon)  # avec transparence
    
    # Exporter en PNG
    buffer = BytesIO()
    img.save(buffer, format="PNG", quality=95)
    buffer.seek(0)
    return buffer.getvalue()
```

### Route FastAPI pour servir l'image

```python
# routers/og.py

from fastapi import Response
from services.og_generator import generate_og_card

# Cache simple en mémoire (dict) — remplacer par Redis en V2
og_cache: dict[str, tuple[bytes, float]] = {}
OG_CACHE_TTL = 6 * 3600  # 6 heures

@app.get("/api/og/{slug}.png")
async def og_image(slug: str):
    # Vérifier le cache
    if slug in og_cache:
        data, cached_at = og_cache[slug]
        if time.time() - cached_at < OG_CACHE_TTL:
            return Response(content=data, media_type="image/png")
    
    player = await get_player_by_slug(slug)
    if not player:
        return Response(status_code=404)
    
    image_bytes = await generate_og_card(player)
    og_cache[slug] = (image_bytes, time.time())
    
    return Response(
        content=image_bytes,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=21600"}  # 6h
    )
```

---

## 8. API Backend — Endpoints

### Joueurs

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/players` | Créer un profil (body: riot_id + données déclaratives) |
| `GET` | `/api/players/{slug}` | Récupérer un profil complet |
| `PATCH` | `/api/players/{slug}` | Mettre à jour les données déclaratives |
| `POST` | `/api/players/{slug}/refresh` | Forcer un rafraîchissement des données Riot |
| `DELETE` | `/api/players/{slug}` | Supprimer un profil |

### Browse / Recherche

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/players?is_lft=true&role=JUNGLE&min_rank=GOLD` | Lister les joueurs LFT avec filtres |

### OG

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/og/{slug}.png` | Image OG générée dynamiquement |

### Riot (interne)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/riot/check/{name}/{tag}` | Vérifier si un Riot ID existe (utilisé par le formulaire) |

---

## 9. Frontend Vue — Pages et Composants

### Pages

| Route | Vue | Description |
|-------|-----|-------------|
| `/` | `Home.vue` | Landing page : explication + CTA "Crée ton profil" |
| `/create` | `CreateProfile.vue` | Formulaire de création en étapes |
| `/p/:slug` | `Profile.vue` | Page profil publique |
| `/browse` | `Browse.vue` | Recherche/filtre de joueurs LFT |

### Flow de création de profil (`/create`)

```
Étape 1 — Riot ID                    Étape 2 — Données auto           Étape 3 — Infos perso
┌──────────────────────┐         ┌──────────────────────┐        ┌──────────────────────┐
│                      │         │                      │        │                      │
│  Entre ton Riot ID   │         │  On a trouvé :       │        │  Ton Discord :       │
│                      │         │                      │        │  [_______________]   │
│  [Pseudo ] # [TAG ]  │  ────▶  │  ◆ Emerald 2         │ ────▶  │                      │
│                      │         │  🎯 Jungle Main       │        │  Tu cherches :       │
│  [ Rechercher ]      │         │  🏆 Lee Sin, Vi...    │        │  ○ Team compétitive  │
│                      │         │                      │        │  ○ Team chill         │
│                      │         │  ✅ C'est bien toi ?  │        │  ○ Duo / Clash       │
└──────────────────────┘         │  [Oui, continuer]    │        │                      │
                                 └──────────────────────┘        │  Tes disponibilités: │
                                                                 │  [grille interactive]│
                                                                 │                      │
                                                                 │  Description libre : │
                                                                 │  [_______________]   │
                                                                 │                      │
                                                                 │  [Créer mon profil]  │
                                                                 └──────────────────────┘
                                                                           │
                                                                           ▼
                                                                  Profil créé ! 🎉
                                                                  Ton lien :
                                                                  https://riftteam.gg/p/Pseudo-TAG
                                                                  [ 📋 Copier ] [ 📤 Partager ]
```

---

## 10. Plan de Développement

### Phase 1 — Fondations (Semaines 1-2)
- [ ] Setup projet : FastAPI + PostgreSQL + Alembic + Vue 3 + Vite
- [ ] Docker Compose (PostgreSQL + API + frontend dev)
- [ ] Client Riot API (`shared/riot_client.py`) avec rate limiting
- [ ] Modèle de données + migrations Alembic
- [ ] Endpoints API : création et récupération de profil
- [ ] Service de détection de rôle (`role_detector.py`)

### Phase 2 — Frontend + OG (Semaines 3-4)
- [ ] Page de création de profil (flow en 3 étapes)
- [ ] Page profil publique
- [ ] Génération d'image OG avec Pillow
- [ ] Route OG avec meta tags pour les crawlers Discord
- [ ] Page browse/recherche avec filtres
- [ ] Cron job de rafraîchissement des données Riot

### Phase 3 — Bot Discord (Semaines 5-6)
- [ ] Setup bot discord.py
- [ ] Commande `/profil` avec embed riche
- [ ] Commande `/lft` (liste des joueurs en recherche, filtrée par rôle)
- [ ] Commande `/setup` pour les admins (channel dédié)
- [ ] Hébergement du bot

### Phase 4 — Polish & Lancement (Semaines 7-8)
- [ ] Design soigné (card OG, page profil, landing page)
- [ ] Tests avec un groupe restreint de joueurs FR
- [ ] Soumission à Riot pour la clé Production
- [ ] Démarche auprès des admins des serveurs Discord FR
- [ ] Monitoring basique (logs, erreurs API)

### Phase 5 — Post-lancement (Semaines 9+)
- [ ] Intégration RSO (quand approuvé par Riot) → badge "compte vérifié"
- [ ] Profils d'équipes (LFP)
- [ ] Système de réputation / reviews
- [ ] Notifications Discord (matching automatique)
- [ ] App Overwolf / overlay (V3+)

---

## 11. Go-to-Market — Communauté FR

### Serveurs Discord cibles

| Serveur | Membres (estimé) | Intérêt |
|---------|-------------------|---------|
| League of Legends FR | 50k+ | Le plus gros serveur FR LoL, channels LFT/LFP existants |
| FFR Community | 10k+ | Communauté FR active, orientée recrutement |
| Serveurs de ligues amateurs FR | Variable | Nexus Tour, ligues communautaires |
| Serveurs de streamers FR LoL | Variable | Audience captive de joueurs motivés |

### Argumentaire pour les admins

> "RiftTeam est un bot gratuit qui améliore vos channels joueur-cherche-équipe. Au lieu de messages texte en vrac, vos membres partagent des profils avec rang réel tiré de l'API Riot, champions joués, et disponibilités — le tout dans un embed propre et standardisé. Ça vous enlève du travail de modération et ça améliore l'expérience de vos membres."

### Boucle de croissance virale

```
Joueur crée son profil (60 secondes)
       │
       ▼
Poste le lien dans un channel Discord
       │
       ▼
L'embed est visuellement supérieur aux messages texte
       │
       ▼
D'autres joueurs : "C'est quoi ce truc ?"
       │
       ▼
Ils créent leur propre profil
       │
       ▼
L'admin du serveur installe le bot
       │
       ▼
Le bot devient un standard sur le serveur
```

Chaque embed partagé est une pub pour la plateforme. Le lien `riftteam.gg` est visible dans chaque card.

---

## 12. Roadmap Futures (Hors V1)

### V2 — Matching & Réputation
- Matching automatique : notifier quand un profil compatible apparaît
- Reviews après tryout (attitude, ponctualité, niveau réel)
- Score de fiabilité visible sur le profil

### V3 — Équipes & Scrims
- Profils d'équipes avec roster complet
- Scrim scheduler avec matching par rang
- Calendrier partagé d'équipe

### V4 — Écosystème compétitif FR
- Intégration circuit amateur (Nexus Tour, Coupe de France)
- Historique de tournois
- Leaderboard communautaire

---

*Document généré le 16/02/2026 — RiftTeam V1 Architecture Spec*
*Stack : Vue 3 + Vite | FastAPI (Python) | PostgreSQL | discord.py | Pillow*
