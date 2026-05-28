# 🚀 Razy HUB Bot — Guide d'installation

## 📁 Structure du projet
```
bot/
├── main.py              # Fichier principal
├── requirements.txt     # Dépendances
├── .env                 # Token Discord (à créer)
├── razy.db              # Base de données SQLite (auto-générée)
└── cogs/
    ├── tickets.py       # Système de tickets complet
    ├── moderation.py    # Modération complète
    ├── automod.py       # Anti-lien & AutoMod
    └── utility.py       # Leveling, Giveaway, Utilitaires
```

## ⚙️ Installation

### 1. Prérequis
- Python 3.10+
- Un bot Discord avec les intents activés sur https://discord.com/developers

### 2. Intents requis (portal Discord)
✅ PRESENCE INTENT
✅ SERVER MEMBERS INTENT
✅ MESSAGE CONTENT INTENT

### 3. Setup
```bash
# Installer les dépendances
pip install -r requirements.txt

# Créer le fichier .env
echo "DISCORD_TOKEN=ton_token_ici" > .env

# Lancer le bot
python main.py
```

## 🎮 Commandes disponibles

### 🎫 Tickets
| Commande | Description | Permission |
|----------|-------------|------------|
| `/ticket-panel` | Déployer le panel de tickets | Admin |
| `/ticket-config` | Configurer catégorie/logs/rôle staff | Admin |
| `/ticket-add` | Ajouter un membre au ticket | Manage Channels |
| `/ticket-remove` | Retirer un membre du ticket | Manage Channels |
| `/ticket-list` | Liste des tickets ouverts | Manage Channels |

### 🔨 Modération
| Commande | Description | Permission |
|----------|-------------|------------|
| `/ban` | Bannir (avec raison + purge messages) | Ban Members |
| `/unban` | Débannir par ID | Ban Members |
| `/banlist` | Liste des bannis | Ban Members |
| `/kick` | Expulser | Kick Members |
| `/mute` | Timeout Discord (10m, 1h, 2d...) | Moderate Members |
| `/unmute` | Retirer le timeout | Moderate Members |
| `/warn` | Avertir (auto-sanction à 3/5 warns) | Manage Messages |
| `/warns` | Voir les warns d'un membre | - |
| `/unwarn` | Supprimer un warn par ID | Manage Messages |
| `/clearwarns` | Effacer tous les warns | Admin |

### 🛡️ AutoMod
| Commande | Description | Permission |
|----------|-------------|------------|
| `/antilink` | Activer/configurer l'anti-lien | Admin |
| `/antilink-whitelist` | Whitelist rôles/salons | Admin |
| `/antilink-status` | Voir la config anti-lien | Manage Messages |
| `/automod` | Configurer anti-spam/caps/mentions | Admin |

### 🎉 Events
| Commande | Description | Permission |
|----------|-------------|------------|
| `/giveaway` | Lancer un giveaway | Manage Messages |
| `/giveaway-reroll` | Reroll un giveaway | Manage Messages |
| `/poll` | Créer un sondage | Manage Messages |
| `/reactionrole` | Panel de reaction roles | Manage Roles |

### 📊 Stats & Utilitaires
| Commande | Description | Permission |
|----------|-------------|------------|
| `/level` | Voir son niveau XP | - |
| `/leaderboard` | Top 10 XP du serveur | - |
| `/userinfo` | Infos complètes sur un membre | - |
| `/serverinfo` | Infos sur le serveur | - |
| `/avatar` | Voir l'avatar | - |
| `/ping` | Latence du bot | - |
| `/botinfo` | Infos sur le bot | - |

### ⚙️ Setup
| Commande | Description | Permission |
|----------|-------------|------------|
| `/setup` | Générer le serveur Razy HUB | Admin |
| `/reset` | Reset complet | Admin |
| `/annonce` | Annonce pro avec embed | Manage Messages |
| `/embed` | Embed personnalisé | Manage Messages |
| `/say` | Faire parler le bot | Admin |
| `/clear` | Supprimer des messages | Manage Messages |
| `/lock` / `/unlock` | Verrouiller un salon | Manage Channels |
| `/slowmode` | Slowmode | Manage Channels |
| `/role` | Donner/retirer un rôle | Manage Roles |

## 🔧 Fonctionnalités automatiques
- **Welcome/Leave** : Messages de bienvenue automatiques avec embed
- **Auto-role** : Rôle `👤 Membre` assigné automatiquement
- **Leveling** : +15 XP par message, level up avec notifications
- **Anti-spam** : Mute automatique après X messages en Y secondes
- **Anti-caps** : Suppression si trop de majuscules
- **Anti-mention** : Mute si trop de mentions
- **Auto-ban** : Ban automatique à 5 warns, mute à 3 warns
- **Transcripts HTML** : Générés automatiquement à la fermeture des tickets

## 📝 Notes importantes
- La DB SQLite est créée automatiquement au premier démarrage
- Les reaction roles persistent en DB (résistent aux redémarrages)
- Les views de tickets sont persistantes (persistent views)
- Les transcripts HTML sont stylés façon Discord
