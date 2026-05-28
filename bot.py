import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} est connecté!")
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} commande(s) slash synchronisée(s)")
    except Exception as e:
        print(f"❌ Erreur sync: {e}")

@bot.tree.command(name="setup", description="🚀 Génère le serveur Razy HUB complet")
@app_commands.checks.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild

    await interaction.followup.send("⏳ Génération du serveur **Razy HUB** en cours...", ephemeral=True)

    # --- Supprime les catégories/channels existants ---
    for channel in guild.channels:
        try:
            await channel.delete()
        except:
            pass

    # --- Supprime les rôles existants (sauf @everyone) ---
    for role in guild.roles:
        if role.name != "@everyone" and not role.managed:
            try:
                await role.delete()
            except:
                pass

    await asyncio.sleep(1)

    # ===================== ROLES =====================
    role_owner = await guild.create_role(
        name="👑 Owner",
        color=discord.Color.from_rgb(255, 215, 0),
        hoist=True,
        permissions=discord.Permissions.all()
    )
    role_admin = await guild.create_role(
        name="⚡ Administrateur",
        color=discord.Color.from_rgb(220, 20, 60),
        hoist=True,
        permissions=discord.Permissions(
            administrator=True
        )
    )
    role_staff = await guild.create_role(
        name="🛡️ Staff",
        color=discord.Color.from_rgb(255, 140, 0),
        hoist=True,
        permissions=discord.Permissions(
            manage_messages=True,
            kick_members=True,
            mute_members=True
        )
    )
    role_vip = await guild.create_role(
        name="💎 VIP",
        color=discord.Color.from_rgb(0, 191, 255),
        hoist=True,
        permissions=discord.Permissions(
            send_messages=True,
            read_messages=True
        )
    )
    role_acheteur = await guild.create_role(
        name="🛒 Acheteur",
        color=discord.Color.from_rgb(50, 205, 50),
        hoist=True,
        permissions=discord.Permissions(
            send_messages=True,
            read_messages=True
        )
    )
    role_membre = await guild.create_role(
        name="👤 Membre",
        color=discord.Color.from_rgb(150, 150, 150),
        hoist=True,
        permissions=discord.Permissions(
            send_messages=True,
            read_messages=True,
            add_reactions=True
        )
    )

    await asyncio.sleep(1)

    # Overwrites par défaut (everyone ne voit rien)
    everyone = guild.default_role
    ow_lock = {
        everyone: discord.PermissionOverwrite(read_messages=False)
    }
    ow_public = {
        everyone: discord.PermissionOverwrite(read_messages=True, send_messages=False),
        role_membre: discord.PermissionOverwrite(read_messages=True, send_messages=False),
    }
    ow_chat = {
        everyone: discord.PermissionOverwrite(read_messages=False),
        role_membre: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        role_acheteur: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        role_vip: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        role_staff: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        role_admin: discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }
    ow_acheteur = {
        everyone: discord.PermissionOverwrite(read_messages=False),
        role_acheteur: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        role_vip: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        role_staff: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        role_admin: discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }
    ow_staff = {
        everyone: discord.PermissionOverwrite(read_messages=False),
        role_staff: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        role_admin: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        role_owner: discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }

    # ===================== CATÉGORIES & CHANNELS =====================

    # 📌 INFORMATIONS
    cat_info = await guild.create_category("📌 ── INFORMATIONS ──", overwrites=ow_lock)
    await guild.create_text_channel("🏠│accueil", category=cat_info, overwrites=ow_public,
        topic="Bienvenue sur le serveur officiel de Razy HUB 🚀")
    await guild.create_text_channel("📜│règlement", category=cat_info, overwrites=ow_public,
        topic="Règles du serveur à respecter")
    await guild.create_text_channel("📣│annonces", category=cat_info, overwrites=ow_public,
        topic="Annonces officielles de Razy HUB")
    await guild.create_text_channel("🔄│mises-à-jour", category=cat_info, overwrites=ow_public,
        topic="Changelogs et mises à jour des scripts")

    # 🛒 BOUTIQUE
    cat_shop = await guild.create_category("🛒 ── BOUTIQUE ──", overwrites=ow_lock)
    await guild.create_text_channel("💰│prix-et-produits", category=cat_shop, overwrites=ow_public,
        topic="Liste des scripts disponibles à l'achat")
    await guild.create_text_channel("🎁│promotions", category=cat_shop, overwrites=ow_public,
        topic="Offres spéciales et réductions")
    await guild.create_text_channel("🛍️│comment-acheter", category=cat_shop, overwrites=ow_public,
        topic="Guide d'achat step-by-step")

    # 💬 COMMUNAUTÉ
    cat_comm = await guild.create_category("💬 ── COMMUNAUTÉ ──", overwrites=ow_lock)
    await guild.create_text_channel("💬│général", category=cat_comm, overwrites=ow_chat,
        topic="Discussion générale")
    await guild.create_text_channel("🤝│présentations", category=cat_comm, overwrites=ow_chat,
        topic="Présente-toi à la communauté!")
    await guild.create_text_channel("🎮│off-topic", category=cat_comm, overwrites=ow_chat,
        topic="Discussion libre, hors sujet")
    await guild.create_text_channel("😂│mèmes", category=cat_comm, overwrites=ow_chat,
        topic="Partage tes mèmes préférés")
    await guild.create_voice_channel("🔊 Général", category=cat_comm)
    await guild.create_voice_channel("🎮 Gaming", category=cat_comm)

    # 🔐 ESPACE ACHETEURS
    cat_buy = await guild.create_category("🔐 ── ESPACE ACHETEURS ──", overwrites=ow_lock)
    await guild.create_text_channel("📥│téléchargements", category=cat_buy, overwrites=ow_acheteur,
        topic="Téléchargements réservés aux acheteurs")
    await guild.create_text_channel("🔑│licences", category=cat_buy, overwrites=ow_acheteur,
        topic="Gestion de vos licences Razy HUB")
    await guild.create_text_channel("❓│support-script", category=cat_buy, overwrites=ow_acheteur,
        topic="Support technique pour les acheteurs")
    await guild.create_text_channel("💬│lounge-acheteurs", category=cat_buy, overwrites=ow_acheteur,
        topic="Salon privé réservé aux acheteurs")

    # 🎫 SUPPORT
    cat_support = await guild.create_category("🎫 ── SUPPORT ──", overwrites=ow_lock)
    await guild.create_text_channel("📩│ouvrir-un-ticket", category=cat_support, overwrites=ow_chat,
        topic="Ouvre un ticket pour contacter le staff")
    await guild.create_text_channel("❓│faq", category=cat_support, overwrites=ow_public,
        topic="Questions fréquemment posées")

    # ⭐ AVIS
    cat_avis = await guild.create_category("⭐ ── AVIS ──", overwrites=ow_lock)
    await guild.create_text_channel("⭐│avis-clients", category=cat_avis, overwrites=ow_public,
        topic="Avis et témoignages des clients")
    await guild.create_text_channel("📸│showcase", category=cat_avis, overwrites=ow_chat,
        topic="Montre ce que tu as créé avec Razy HUB")

    # 🛡️ STAFF
    cat_staff = await guild.create_category("🛡️ ── STAFF ──", overwrites=ow_lock)
    await guild.create_text_channel("📋│staff-général", category=cat_staff, overwrites=ow_staff,
        topic="Discussion interne du staff")
    await guild.create_text_channel("📊│logs", category=cat_staff, overwrites=ow_staff,
        topic="Logs du bot et des actions")
    await guild.create_text_channel("🚨│sanctions", category=cat_staff, overwrites=ow_staff,
        topic="Sanctions appliquées")
    await guild.create_voice_channel("🛡️ Staff Vocal", category=cat_staff,
        overwrites=ow_staff)

    await asyncio.sleep(1)

    # Donne le rôle Owner à celui qui a lancé la commande
    try:
        await interaction.user.add_roles(role_owner, role_admin)
    except:
        pass

    # ===================== MESSAGES D'ACCUEIL =====================
    for ch in guild.text_channels:
        if "accueil" in ch.name:
            embed = discord.Embed(
                title="🚀 Bienvenue sur **Razy HUB**",
                description=(
                    "> Le serveur officiel de vente de scripts premium.\n\n"
                    "**Razy HUB** c'est quoi ?\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    "🔥 Des scripts de haute qualité\n"
                    "💎 Un support dédié et réactif\n"
                    "🔄 Des mises à jour régulières\n"
                    "🔐 Licences sécurisées\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "📜 Lis le <#règlement> avant tout\n"
                    "🛒 Consulte la <#💰│prix-et-produits> pour nos offres\n"
                    "🎫 Besoin d'aide ? Ouvre un ticket !"
                ),
                color=discord.Color.from_rgb(255, 60, 60)
            )
            embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)
            embed.set_footer(text="Razy HUB • Scripts Premium", icon_url=guild.icon.url if guild.icon else discord.Embed.Empty)
            embed.set_image(url="https://i.imgur.com/placeholder.png")
            await ch.send(embed=embed)
            break

    for ch in guild.text_channels:
        if "règlement" in ch.name or "reglement" in ch.name:
            embed = discord.Embed(
                title="📜 Règlement — Razy HUB",
                description=(
                    "Merci de respecter les règles suivantes sous peine de sanction.\n\n"
                    "**Article 1 — Respect**\n"
                    "> Toute forme d'insulte, harcèlement ou discrimination est interdite.\n\n"
                    "**Article 2 — Spam**\n"
                    "> Le spam, flood et les messages inutiles sont prohibés.\n\n"
                    "**Article 3 — Publicité**\n"
                    "> Aucune publicité sans accord du staff.\n\n"
                    "**Article 4 — Arnaques**\n"
                    "> Toute tentative d'arnaque = ban permanent.\n\n"
                    "**Article 5 — Contenu**\n"
                    "> Contenu NSFW, illégal ou choquant strictement interdit.\n\n"
                    "**Article 6 — Tickets**\n"
                    "> Utilisez les tickets pour les demandes de support.\n\n"
                    "**Article 7 — Droits**\n"
                    "> La revente de nos scripts est strictement interdite.\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    "✅ En restant sur ce serveur, vous acceptez ces règles."
                ),
                color=discord.Color.from_rgb(255, 60, 60)
            )
            embed.set_footer(text="Razy HUB • Scripts Premium")
            await ch.send(embed=embed)
            break

    for ch in guild.text_channels:
        if "prix" in ch.name or "produits" in ch.name:
            embed = discord.Embed(
                title="💰 Nos Scripts — Razy HUB",
                description=(
                    "Découvrez notre catalogue de scripts premium !\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    "🔥 **Razy HUB — Pack Starter**\n"
                    "> Prix : **X€**\n"
                    "> ✅ Script de base + support\n\n"
                    "💎 **Razy HUB — Pack Premium**\n"
                    "> Prix : **X€**\n"
                    "> ✅ Accès complet + mises à jour\n\n"
                    "👑 **Razy HUB — Pack VIP**\n"
                    "> Prix : **X€**\n"
                    "> ✅ Tout inclus + support prioritaire\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    "📩 Pour acheter → ouvre un ticket !"
                ),
                color=discord.Color.from_rgb(255, 215, 0)
            )
            embed.set_footer(text="Razy HUB • Scripts Premium")
            await ch.send(embed=embed)
            break

    await interaction.followup.send(
        "✅ **Serveur Razy HUB généré avec succès !**\n"
        "📌 Catégories, channels, rôles et messages créés.\n"
        "👑 Rôle Owner assigné à ton compte.",
        ephemeral=True
    )

bot.run(TOKEN)
