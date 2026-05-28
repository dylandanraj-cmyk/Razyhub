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

async def delete_all(guild: discord.Guild):
    """Supprime tous les channels et rôles existants."""
    tasks = [ch.delete() for ch in guild.channels]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for r in results:
        if isinstance(r, Exception):
            pass  # ignore silently

    for role in guild.roles:
        if role.name != "@everyone" and not role.managed:
            try:
                await role.delete()
            except:
                pass

async def create_roles(guild: discord.Guild):
    """Crée tous les rôles Razy HUB."""
    role_owner = await guild.create_role(
        name="👑 Owner", color=discord.Color.from_rgb(255, 215, 0),
        hoist=True, permissions=discord.Permissions.all()
    )
    role_admin = await guild.create_role(
        name="⚡ Administrateur", color=discord.Color.from_rgb(220, 20, 60),
        hoist=True, permissions=discord.Permissions(administrator=True)
    )
    role_staff = await guild.create_role(
        name="🛡️ Staff", color=discord.Color.from_rgb(255, 140, 0),
        hoist=True, permissions=discord.Permissions(
            manage_messages=True, kick_members=True, mute_members=True,
            read_messages=True, send_messages=True
        )
    )
    role_vip = await guild.create_role(
        name="💎 VIP", color=discord.Color.from_rgb(0, 191, 255),
        hoist=True, permissions=discord.Permissions(read_messages=True, send_messages=True)
    )
    role_acheteur = await guild.create_role(
        name="🛒 Acheteur", color=discord.Color.from_rgb(50, 205, 50),
        hoist=True, permissions=discord.Permissions(read_messages=True, send_messages=True)
    )
    role_membre = await guild.create_role(
        name="👤 Membre", color=discord.Color.from_rgb(150, 150, 150),
        hoist=True, permissions=discord.Permissions(
            read_messages=True, send_messages=True, add_reactions=True
        )
    )
    return role_owner, role_admin, role_staff, role_vip, role_acheteur, role_membre

async def send_accueil(channel, guild):
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
            "📜 Lis le règlement avant tout\n"
            "🛒 Consulte la boutique pour nos offres\n"
            "🎫 Besoin d'aide ? Ouvre un ticket !"
        ),
        color=discord.Color.from_rgb(255, 60, 60)
    )
    embed.set_footer(text="Razy HUB • Scripts Premium")
    await channel.send(embed=embed)

async def send_reglement(channel):
    embed = discord.Embed(
        title="📜 Règlement — Razy HUB",
        description=(
            "Respecte ces règles sous peine de sanction.\n\n"
            "**Article 1 — Respect**\n"
            "> Insultes, harcèlement, discrimination = sanction immédiate.\n\n"
            "**Article 2 — Spam**\n"
            "> Spam, flood, messages inutiles interdits.\n\n"
            "**Article 3 — Publicité**\n"
            "> Aucune pub sans accord du staff.\n\n"
            "**Article 4 — Arnaques**\n"
            "> Tentative d'arnaque = ban permanent.\n\n"
            "**Article 5 — Contenu**\n"
            "> Contenu NSFW, illégal ou choquant = ban.\n\n"
            "**Article 6 — Revente**\n"
            "> La revente de nos scripts est strictement interdite.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ En restant sur ce serveur, vous acceptez ces règles."
        ),
        color=discord.Color.from_rgb(255, 60, 60)
    )
    embed.set_footer(text="Razy HUB • Scripts Premium")
    await channel.send(embed=embed)

async def send_prix(channel):
    embed = discord.Embed(
        title="💰 Nos Scripts — Razy HUB",
        description=(
            "Découvrez notre catalogue de scripts premium !\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔥 **Pack Starter**\n"
            "> Prix : **X€** — Script de base + support\n\n"
            "💎 **Pack Premium**\n"
            "> Prix : **X€** — Accès complet + mises à jour\n\n"
            "👑 **Pack VIP**\n"
            "> Prix : **X€** — Tout inclus + support prioritaire\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📩 Pour acheter → ouvre un ticket !"
        ),
        color=discord.Color.from_rgb(255, 215, 0)
    )
    embed.set_footer(text="Razy HUB • Scripts Premium")
    await channel.send(embed=embed)

@bot.tree.command(name="setup", description="🚀 Génère le serveur Razy HUB complet")
@app_commands.checks.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    # Defer IMMÉDIATEMENT — doit être fait en < 3 secondes
    await interaction.response.defer(ephemeral=True)

    guild = interaction.guild

    try:
        # === 1. Suppression ===
        await delete_all(guild)

        # === 2. Rôles ===
        role_owner, role_admin, role_staff, role_vip, role_acheteur, role_membre = await create_roles(guild)
        everyone = guild.default_role

        # === 3. Permissions ===
        ow_public = {
            everyone: discord.PermissionOverwrite(read_messages=True, send_messages=False),
        }
        ow_chat = {
            everyone: discord.PermissionOverwrite(read_messages=False),
            role_membre:   discord.PermissionOverwrite(read_messages=True, send_messages=True),
            role_acheteur: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            role_vip:      discord.PermissionOverwrite(read_messages=True, send_messages=True),
            role_staff:    discord.PermissionOverwrite(read_messages=True, send_messages=True),
            role_admin:    discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        ow_acheteur = {
            everyone:      discord.PermissionOverwrite(read_messages=False),
            role_acheteur: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            role_vip:      discord.PermissionOverwrite(read_messages=True, send_messages=True),
            role_staff:    discord.PermissionOverwrite(read_messages=True, send_messages=True),
            role_admin:    discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        ow_staff = {
            everyone:   discord.PermissionOverwrite(read_messages=False),
            role_staff: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            role_admin: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            role_owner: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        # === 4. Catégories & Channels ===

        # 📌 INFORMATIONS
        cat_info = await guild.create_category("📌 ── INFORMATIONS ──", overwrites={everyone: discord.PermissionOverwrite(read_messages=True)})
        ch_accueil  = await guild.create_text_channel("🏠│accueil",      category=cat_info, overwrites=ow_public)
        ch_reglement = await guild.create_text_channel("📜│règlement",   category=cat_info, overwrites=ow_public)
        await guild.create_text_channel("📣│annonces",                   category=cat_info, overwrites=ow_public)
        await guild.create_text_channel("🔄│mises-à-jour",              category=cat_info, overwrites=ow_public)

        # 🛒 BOUTIQUE
        cat_shop = await guild.create_category("🛒 ── BOUTIQUE ──", overwrites={everyone: discord.PermissionOverwrite(read_messages=True)})
        ch_prix = await guild.create_text_channel("💰│prix-et-produits", category=cat_shop, overwrites=ow_public)
        await guild.create_text_channel("🎁│promotions",                 category=cat_shop, overwrites=ow_public)
        await guild.create_text_channel("🛍️│comment-acheter",          category=cat_shop, overwrites=ow_public)

        # 💬 COMMUNAUTÉ
        cat_comm = await guild.create_category("💬 ── COMMUNAUTÉ ──", overwrites={everyone: discord.PermissionOverwrite(read_messages=False)})
        await guild.create_text_channel("💬│général",       category=cat_comm, overwrites=ow_chat)
        await guild.create_text_channel("🤝│présentations", category=cat_comm, overwrites=ow_chat)
        await guild.create_text_channel("🎮│off-topic",     category=cat_comm, overwrites=ow_chat)
        await guild.create_text_channel("😂│mèmes",         category=cat_comm, overwrites=ow_chat)
        await guild.create_voice_channel("🔊 Général", category=cat_comm)
        await guild.create_voice_channel("🎮 Gaming",  category=cat_comm)

        # 🔐 ACHETEURS
        cat_buy = await guild.create_category("🔐 ── ESPACE ACHETEURS ──", overwrites={everyone: discord.PermissionOverwrite(read_messages=False)})
        await guild.create_text_channel("📥│téléchargements", category=cat_buy, overwrites=ow_acheteur)
        await guild.create_text_channel("🔑│licences",        category=cat_buy, overwrites=ow_acheteur)
        await guild.create_text_channel("❓│support-script",  category=cat_buy, overwrites=ow_acheteur)
        await guild.create_text_channel("💬│lounge-acheteurs",category=cat_buy, overwrites=ow_acheteur)

        # 🎫 SUPPORT
        cat_sup = await guild.create_category("🎫 ── SUPPORT ──", overwrites={everyone: discord.PermissionOverwrite(read_messages=False)})
        await guild.create_text_channel("📩│ouvrir-un-ticket", category=cat_sup, overwrites=ow_chat)
        await guild.create_text_channel("❓│faq",              category=cat_sup, overwrites=ow_public)

        # ⭐ AVIS
        cat_avis = await guild.create_category("⭐ ── AVIS ──", overwrites={everyone: discord.PermissionOverwrite(read_messages=True)})
        await guild.create_text_channel("⭐│avis-clients", category=cat_avis, overwrites=ow_public)
        await guild.create_text_channel("📸│showcase",     category=cat_avis, overwrites=ow_chat)

        # 🛡️ STAFF
        cat_staff = await guild.create_category("🛡️ ── STAFF ──", overwrites={everyone: discord.PermissionOverwrite(read_messages=False)})
        await guild.create_text_channel("📋│staff-général", category=cat_staff, overwrites=ow_staff)
        await guild.create_text_channel("📊│logs",          category=cat_staff, overwrites=ow_staff)
        await guild.create_text_channel("🚨│sanctions",     category=cat_staff, overwrites=ow_staff)
        await guild.create_voice_channel("🛡️ Staff Vocal",  category=cat_staff, overwrites=ow_staff)

        # === 5. Messages d'accueil ===
        await send_accueil(ch_accueil, guild)
        await send_reglement(ch_reglement)
        await send_prix(ch_prix)

        # === 6. Rôle Owner à l'utilisateur ===
        try:
            await interaction.user.add_roles(role_owner, role_admin)
        except:
            pass

        await interaction.followup.send(
            "✅ **Serveur Razy HUB généré avec succès !**\n"
            "📌 Catégories, channels, rôles et messages créés.\n"
            "👑 Rôle Owner assigné à ton compte.",
            ephemeral=True
        )

    except Exception as e:
        await interaction.followup.send(f"❌ Erreur lors de la génération : `{e}`", ephemeral=True)
        print(f"Erreur setup: {e}")

@setup.error
async def setup_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Tu dois être **Administrateur** pour utiliser cette commande.", ephemeral=True)

bot.run(TOKEN)
