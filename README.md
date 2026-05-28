# 🚀 Razy HUB — Bot Discord

Bot Discord qui génère automatiquement ton serveur **Razy HUB** complet avec catégories, channels, rôles et messages d'accueil.

---

## 📋 Ce que le bot crée

### 🎭 Rôles
| Rôle | Couleur | Description |
|------|---------|-------------|
| 👑 Owner | Or | Propriétaire du serveur |
| ⚡ Administrateur | Rouge | Admin complet |
| 🛡️ Staff | Orange | Modérateurs |
| 💎 VIP | Bleu ciel | Membres VIP |
| 🛒 Acheteur | Vert | Clients ayant acheté |
| 👤 Membre | Gris | Membres de base |

### 📁 Catégories & Channels
- **📌 INFORMATIONS** — accueil, règlement, annonces, mises-à-jour
- **🛒 BOUTIQUE** — prix, promotions, comment acheter
- **💬 COMMUNAUTÉ** — général, présentations, off-topic, mèmes + vocaux
- **🔐 ESPACE ACHETEURS** — téléchargements, licences, support, lounge
- **🎫 SUPPORT** — tickets, faq
- **⭐ AVIS** — avis clients, showcase
- **🛡️ STAFF** — staff général, logs, sanctions + vocal

---

## ⚙️ Installation

### Étape 1 — Créer le bot Discord

1. Va sur [Discord Developer Portal](https://discord.com/developers/applications)
2. Clique **New Application** → nom : `Razy HUB`
3. Va dans **Bot** → clique **Add Bot**
4. Active ces **Privileged Gateway Intents** :
   - ✅ Server Members Intent
   - ✅ Message Content Intent
5. Copie le **Token** du bot
6. Va dans **OAuth2 > URL Generator** :
   - Coche `bot` + `applications.commands`
   - Permissions : `Administrator`
   - Copie le lien et invite le bot sur ton serveur

### Étape 2 — Cloner le projet

```bash
git clone https://github.com/TON_USERNAME/razy-hub-bot.git
cd razy-hub-bot
```

### Étape 3 — Configurer le .env (local)

```bash
cp .env.example .env
# Édite .env et colle ton token Discord
```

### Étape 4 — Installer les dépendances (local)

```bash
pip install -r requirements.txt
python bot.py
```

---

## 🚂 Déploiement sur Railway

### Étape 1 — Push sur GitHub

```bash
git init
git add .
git commit -m "🚀 Initial commit — Razy HUB Bot"
git branch -M main
git remote add origin https://github.com/TON_USERNAME/razy-hub-bot.git
git push -u origin main
```

### Étape 2 — Déployer sur Railway

1. Va sur [railway.app](https://railway.app) et connecte-toi avec GitHub
2. Clique **New Project** → **Deploy from GitHub repo**
3. Sélectionne ton repo `razy-hub-bot`
4. Va dans **Variables** → ajoute :
   ```
   DISCORD_TOKEN = ton_token_ici
   ```
5. Railway détecte automatiquement le `Procfile` et lance `python bot.py`
6. ✅ Ton bot tourne 24h/24 !

---

## 🎮 Utilisation

Une fois le bot en ligne sur ton serveur :

```
/setup
```

> ⚠️ Tu dois avoir les permissions **Administrateur** pour lancer cette commande.

Le bot va :
1. Supprimer les channels/rôles existants
2. Créer toute la structure Razy HUB
3. Envoyer les messages d'accueil dans chaque channel
4. T'assigner le rôle 👑 Owner automatiquement

---

## 📁 Structure du projet

```
razy-hub-bot/
├── bot.py              # Code principal du bot
├── requirements.txt    # Dépendances Python
├── Procfile           # Config Railway
├── .env.example       # Template variables d'environnement
├── .gitignore         # Fichiers ignorés par Git
└── README.md          # Ce fichier
```

---

## 🔧 Personnalisation

Dans `bot.py`, tu peux modifier :
- **Les prix** dans le channel `prix-et-produits`
- **Les noms des channels** selon tes besoins
- **Les couleurs des rôles** (format RGB)
- **Les descriptions des embeds** pour personnaliser ton branding

---

## 📞 Support

Des problèmes ? Rejoins le serveur Razy HUB et ouvre un ticket !
