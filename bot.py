import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
import datetime
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ══════════════════════════════════════════════════
#  COULEURS & CONSTANTES
# ══════════════════════════════════════════════════
RED    = discord.Color.from_rgb(255, 60, 60)
GOLD   = discord.Color.from_rgb(255, 215, 0)
GREEN  = discord.Color.from_rgb(50, 205, 50)
BLUE   = discord.Color.from_rgb(0, 191, 255)
ORANGE = discord.Color.from_rgb(255, 140, 0)
GRAY   = discord.Color.from_rgb(100, 100, 100)

# Stockage des reaction roles (en mémoire, reset au redémarrage)
reaction_roles = {}  # {message_id: {emoji: role_id}}

# ══════════════════════════════════════════════════
#  ON READY
# ══════════════════════════════════════════════════
@bot.event
async def on_ready():
    print(f"✅ {bot.user} connecté!")
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="Razy HUB 🚀")
    )
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} commandes synchronisées")
    except Exception as e:
        print(f"❌ Erreur sync: {e}")

# ══════════════════════════════════════════════════
#  WELCOME SYSTEM
# ══════════════════════════════════════════════════
WELCOME_CHANNEL_NAME = "🌴・welcome"
AUTO_ROLE_NAME = "👤 Membre"

@bot.event
async def on_member_join(member: discord.Member):
    guild = member.guild

    # Auto-role
    role = discord.utils.get(guild.roles, name=AUTO_ROLE_NAME)
    if role:
        try:
            await member.add_roles(role)
        except:
            pass

    # Welcome embed
    channel = discord.utils.get(guild.text_channels, name=WELCOME_CHANNEL_NAME.replace("🌴・", "").strip())
    if not channel:
        for ch in guild.text_channels:
            if "welcome" in ch.name.lower():
                channel = ch
                break

    if channel:
        embed = discord.Embed(
            title=f"🌴 Bienvenue sur Razy HUB !",
            description=(
                f"Hey {member.mention} ! Tu viens d'arriver sur **Razy HUB** 🚀\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎫 Ouvre un ticket pour acheter\n"
                f"📜 Lis les règles du serveur\n"
                f"💬 Présente-toi dans le chat !\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Tu es le **{guild.member_count}ème** membre !"
            ),
            color=GREEN
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Razy HUB • Scripts Premium", icon_url=guild.icon.url if guild.icon else None)
        embed.timestamp = datetime.datetime.utcnow()
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member: discord.Member):
    guild = member.guild
    for ch in guild.text_channels:
        if "welcome" in ch.name.lower():
            embed = discord.Embed(
                title="👋 Départ",
                description=f"**{member.name}** vient de quitter le serveur.\nNous sommes maintenant **{guild.member_count}** membres.",
                color=GRAY
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.timestamp = datetime.datetime.utcnow()
            await ch.send(embed=embed)
            break

# ══════════════════════════════════════════════════
#  REACTION ROLES
# ══════════════════════════════════════════════════
@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.message_id in reaction_roles:
        emoji = str(payload.emoji)
        if emoji in reaction_roles[payload.message_id]:
            guild = bot.get_guild(payload.guild_id)
            role = guild.get_role(reaction_roles[payload.message_id][emoji])
            member = guild.get_member(payload.user_id)
            if role and member and not member.bot:
                await member.add_roles(role)

@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    if payload.message_id in reaction_roles:
        emoji = str(payload.emoji)
        if emoji in reaction_roles[payload.message_id]:
            guild = bot.get_guild(payload.guild_id)
            role = guild.get_role(reaction_roles[payload.message_id][emoji])
            member = guild.get_member(payload.user_id)
            if role and member:
                await member.remove_roles(role)

# ══════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════
async def log(guild: discord.Guild, embed: discord.Embed):
    for ch in guild.text_channels:
        if "logs" in ch.name.lower() or "log" in ch.name.lower():
            await ch.send(embed=embed)
            break

async def delete_all(guild):
    tasks = [ch.delete() for ch in guild.channels]
    await asyncio.gather(*tasks, return_exceptions=True)
    for role in guild.roles:
        if role.name != "@everyone" and not role.managed:
            try:
                await role.delete()
            except:
                pass

async def create_roles(guild):
    owner  = await guild.create_role(name="👑 Owner",  color=GOLD,   hoist=True, permissions=discord.Permissions.all())
    admin  = await guild.create_role(name="⚡ Admin",   color=RED,    hoist=True, permissions=discord.Permissions(administrator=True))
    staff  = await guild.create_role(name="🛡️ Staff",  color=ORANGE, hoist=True, permissions=discord.Permissions(manage_messages=True, kick_members=True, mute_members=True, read_messages=True, send_messages=True))
    vip    = await guild.create_role(name="💎 VIP",     color=BLUE,   hoist=True, permissions=discord.Permissions(read_messages=True, send_messages=True))
    member = await guild.create_role(name="👤 Membre",  color=GRAY,   hoist=True, permissions=discord.Permissions(read_messages=True, send_messages=True, add_reactions=True))
    return owner, admin, staff, vip, member

async def build_server(guild, user):
    await delete_all(guild)
    r_owner, r_admin, r_staff, r_vip, r_member = await create_roles(guild)
    ev = guild.default_role

    pub  = {ev: discord.PermissionOverwrite(read_messages=True,  send_messages=False)}
    chat = {ev: discord.PermissionOverwrite(read_messages=False), r_member: discord.PermissionOverwrite(read_messages=True, send_messages=True), r_vip: discord.PermissionOverwrite(read_messages=True, send_messages=True), r_staff: discord.PermissionOverwrite(read_messages=True, send_messages=True), r_admin: discord.PermissionOverwrite(read_messages=True, send_messages=True), r_owner: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
    staf = {ev: discord.PermissionOverwrite(read_messages=False), r_staff: discord.PermissionOverwrite(read_messages=True, send_messages=True), r_admin: discord.PermissionOverwrite(read_messages=True, send_messages=True), r_owner: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
    hide = {ev: discord.PermissionOverwrite(read_messages=False)}
    open_= {ev: discord.PermissionOverwrite(read_messages=True)}

    cat_sup     = await guild.create_category("Support",  overwrites=hide)
    await guild.create_text_channel("🎫・tickets",  category=cat_sup, overwrites=chat)
    await guild.create_text_channel("❓・faq",      category=cat_sup, overwrites=pub)

    cat_main    = await guild.create_category("Main",     overwrites=open_)
    ch_news     = await guild.create_text_channel("📢・news",            category=cat_main, overwrites=pub)
    ch_purchase = await guild.create_text_channel("🟩・purchase",        category=cat_main, overwrites=pub)
    ch_pix      = await guild.create_text_channel("🟩・comprar-pix",     category=cat_main, overwrites=pub)
    ch_pay      = await guild.create_text_channel("🐴・razy-pay",        category=cat_main, overwrites=pub)
    ch_panel    = await guild.create_text_channel("💎・buy-admin-panel", category=cat_main, overwrites=pub)

    cat_hub     = await guild.create_category("Hub",      overwrites=open_)
    await guild.create_text_channel("⚙️・executors", category=cat_hub, overwrites=pub)
    await guild.create_text_channel("👥・steals",    category=cat_hub, overwrites=pub)

    cat_scripts = await guild.create_category("Scripts",  overwrites=open_)
    ch_razy     = await guild.create_text_channel("🟢・razy-hub", category=cat_scripts, overwrites=pub)
    await guild.create_text_channel("📸・showcase",  category=cat_scripts, overwrites=chat)
    await guild.create_text_channel("✅・proofs",    category=cat_scripts, overwrites=chat)

    cat_lounge  = await guild.create_category("Lounge",   overwrites=hide)
    ch_welcome  = await guild.create_text_channel("🌴・welcome", category=cat_lounge, overwrites=pub)
    ch_chat     = await guild.create_text_channel("☁️・chat",    category=cat_lounge, overwrites=chat)
    await guild.create_voice_channel("📞・vc",   category=cat_lounge)
    await guild.create_voice_channel("RazyHUB", category=cat_lounge)

    cat_stf     = await guild.create_category("Staff",    overwrites=hide)
    await guild.create_text_channel("📋・général",   category=cat_stf, overwrites=staf)
    await guild.create_text_channel("📊・logs",      category=cat_stf, overwrites=staf)
    await guild.create_text_channel("🚨・sanctions", category=cat_stf, overwrites=staf)
    await guild.create_voice_channel("🛡️ Staff VC",  category=cat_stf, overwrites=staf)

    await ch_news.send(embed=discord.Embed(title="📢 Razy HUB — News", description="Bienvenue sur **Razy HUB** !\nToutes les annonces officielles ici.", color=RED).set_footer(text="Razy HUB • Scripts Premium"))
    await ch_welcome.send(embed=discord.Embed(title="🌴 Bienvenue sur Razy HUB !", description="Le serveur officiel de **Razy HUB** — Scripts Roblox premium.\n\n🟢 **Notre script :** `razy-hub`\n\n🛒 **Acheter →** `#purchase`\n🎫 **Support →** `#tickets`\n\n━━━━━━━━━━━━━━━━━━━━━━\n✅ Bon jeu !", color=RED).set_footer(text="Razy HUB • Scripts Premium"))
    await ch_purchase.send(embed=discord.Embed(title="🛒 Nos offres — Razy HUB", description="━━━━━━━━━━━━━━━━━━━━━━\n🔥 **Pack Starter** — X€\n> Accès Razy HUB de base\n\n💎 **Pack Premium** — X€\n> Accès complet + mises à jour\n\n👑 **Pack VIP** — X€\n> Tout inclus + support prioritaire\n\n━━━━━━━━━━━━━━━━━━━━━━\n📩 Ouvre un ticket pour acheter !", color=GOLD).set_footer(text="Razy HUB • Scripts Premium"))
    await ch_razy.send(embed=discord.Embed(title="🟢 Razy HUB", description="Le script officiel **Razy HUB**.\n\n> Toutes les infos, loadstring et mises à jour ici.\n\n📥 Achète dans `#purchase` pour y accéder.", color=GREEN).set_footer(text="Razy HUB • Scripts Premium"))

    try:
        await user.add_roles(r_owner, r_admin)
    except:
        pass

# ══════════════════════════════════════════════════
#  SETUP / RESET
# ══════════════════════════════════════════════════
@bot.tree.command(name="setup", description="🚀 Génère le serveur Razy HUB")
@app_commands.checks.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        await build_server(interaction.guild, interaction.user)
        await interaction.followup.send("✅ **Serveur Razy HUB généré !** 👑 Rôle Owner assigné.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Erreur : `{e}`", ephemeral=True)

@bot.tree.command(name="reset", description="🔄 Reset COMPLET du serveur")
@app_commands.checks.has_permissions(administrator=True)
async def reset(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        await build_server(interaction.guild, interaction.user)
        await interaction.followup.send("🔄 **Reset terminé !** Tout recréé proprement. 👑 Rôle Owner réassigné.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Erreur : `{e}`", ephemeral=True)

# ══════════════════════════════════════════════════
#  ANNONCE PROPRE
# ══════════════════════════════════════════════════
@bot.tree.command(name="annonce", description="📢 Faire une annonce pro avec embed")
@app_commands.describe(
    titre="Titre de l'annonce",
    message="Contenu de l'annonce",
    mention="Mentionner @everyone ou @here ? (none/everyone/here)",
    couleur="Couleur : rouge / or / vert / bleu / orange"
)
@app_commands.checks.has_permissions(manage_messages=True)
async def annonce(interaction: discord.Interaction, titre: str, message: str, mention: str = "none", couleur: str = "rouge"):
    couleurs = {"rouge": RED, "or": GOLD, "vert": GREEN, "bleu": BLUE, "orange": ORANGE}
    color = couleurs.get(couleur.lower(), RED)

    embed = discord.Embed(title=f"📢 {titre}", description=message, color=color)
    embed.set_author(name="Razy HUB — Annonce Officielle", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
    embed.set_footer(text=f"Annoncé par {interaction.user.display_name} • Razy HUB", icon_url=interaction.user.display_avatar.url)
    embed.timestamp = datetime.datetime.utcnow()

    ping = ""
    if mention == "everyone":
        ping = "@everyone"
    elif mention == "here":
        ping = "@here"

    await interaction.response.send_message("✅ Annonce envoyée !", ephemeral=True)
    await interaction.channel.send(content=ping if ping else None, embed=embed)

    log_embed = discord.Embed(title="📢 Annonce envoyée", description=f"Par {interaction.user.mention} dans {interaction.channel.mention}\n**Titre :** {titre}", color=BLUE, timestamp=datetime.datetime.utcnow())
    await log(interaction.guild, log_embed)

# ══════════════════════════════════════════════════
#  MODÉRATION — BAN / UNBAN / KICK / MUTE / WARN
# ══════════════════════════════════════════════════
@bot.tree.command(name="ban", description="🔨 Bannir un membre")
@app_commands.describe(membre="Membre à bannir", raison="Raison du ban")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison fournie"):
    if membre.top_role >= interaction.user.top_role:
        await interaction.response.send_message("❌ Tu ne peux pas bannir ce membre.", ephemeral=True)
        return

    try:
        await membre.send(embed=discord.Embed(title="🔨 Tu as été banni", description=f"**Serveur :** {interaction.guild.name}\n**Raison :** {raison}\n**Par :** {interaction.user}", color=RED))
    except:
        pass

    await membre.ban(reason=raison)
    embed = discord.Embed(title="🔨 Membre banni", description=f"**Membre :** {membre} (`{membre.id}`)\n**Raison :** {raison}\n**Par :** {interaction.user.mention}", color=RED, timestamp=datetime.datetime.utcnow())
    await interaction.response.send_message(embed=embed)
    await log(interaction.guild, embed)

@bot.tree.command(name="unban", description="✅ Débannir un utilisateur")
@app_commands.describe(user_id="ID de l'utilisateur à débannir")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user_id: str):
    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user)
        embed = discord.Embed(title="✅ Membre débanni", description=f"**Membre :** {user} (`{user_id}`)\n**Par :** {interaction.user.mention}", color=GREEN, timestamp=datetime.datetime.utcnow())
        await interaction.response.send_message(embed=embed)
        await log(interaction.guild, embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erreur : `{e}`", ephemeral=True)

@bot.tree.command(name="kick", description="👢 Expulser un membre")
@app_commands.describe(membre="Membre à kick", raison="Raison")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison fournie"):
    if membre.top_role >= interaction.user.top_role:
        await interaction.response.send_message("❌ Tu ne peux pas kick ce membre.", ephemeral=True)
        return
    try:
        await membre.send(embed=discord.Embed(title="👢 Tu as été expulsé", description=f"**Serveur :** {interaction.guild.name}\n**Raison :** {raison}", color=ORANGE))
    except:
        pass
    await membre.kick(reason=raison)
    embed = discord.Embed(title="👢 Membre expulsé", description=f"**Membre :** {membre}\n**Raison :** {raison}\n**Par :** {interaction.user.mention}", color=ORANGE, timestamp=datetime.datetime.utcnow())
    await interaction.response.send_message(embed=embed)
    await log(interaction.guild, embed)

@bot.tree.command(name="mute", description="🔇 Rendre muet un membre")
@app_commands.describe(membre="Membre à mute", duree="Durée en minutes", raison="Raison")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, membre: discord.Member, duree: int = 10, raison: str = "Aucune raison fournie"):
    if membre.top_role >= interaction.user.top_role:
        await interaction.response.send_message("❌ Tu ne peux pas mute ce membre.", ephemeral=True)
        return
    until = datetime.datetime.utcnow() + datetime.timedelta(minutes=duree)
    await membre.timeout(until, reason=raison)
    embed = discord.Embed(title="🔇 Membre mute", description=f"**Membre :** {membre.mention}\n**Durée :** {duree} minutes\n**Raison :** {raison}\n**Par :** {interaction.user.mention}", color=ORANGE, timestamp=datetime.datetime.utcnow())
    await interaction.response.send_message(embed=embed)
    await log(interaction.guild, embed)

@bot.tree.command(name="unmute", description="🔊 Retirer le mute d'un membre")
@app_commands.describe(membre="Membre à unmute")
@app_commands.checks.has_permissions(moderate_members=True)
async def unmute(interaction: discord.Interaction, membre: discord.Member):
    await membre.timeout(None)
    embed = discord.Embed(title="🔊 Membre unmute", description=f"**Membre :** {membre.mention}\n**Par :** {interaction.user.mention}", color=GREEN, timestamp=datetime.datetime.utcnow())
    await interaction.response.send_message(embed=embed)
    await log(interaction.guild, embed)

@bot.tree.command(name="warn", description="⚠️ Avertir un membre")
@app_commands.describe(membre="Membre à warn", raison="Raison")
@app_commands.checks.has_permissions(manage_messages=True)
async def warn(interaction: discord.Interaction, membre: discord.Member, raison: str):
    try:
        await membre.send(embed=discord.Embed(title="⚠️ Avertissement", description=f"**Serveur :** {interaction.guild.name}\n**Raison :** {raison}\n**Par :** {interaction.user}", color=ORANGE))
    except:
        pass
    embed = discord.Embed(title="⚠️ Membre averti", description=f"**Membre :** {membre.mention}\n**Raison :** {raison}\n**Par :** {interaction.user.mention}", color=ORANGE, timestamp=datetime.datetime.utcnow())
    await interaction.response.send_message(embed=embed)
    await log(interaction.guild, embed)

# ══════════════════════════════════════════════════
#  CLEAR / LOCK / UNLOCK / SLOWMODE
# ══════════════════════════════════════════════════
@bot.tree.command(name="clear", description="🧹 Supprimer des messages")
@app_commands.describe(nombre="Nombre de messages à supprimer (max 100)")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, nombre: int):
    if nombre < 1 or nombre > 100:
        await interaction.response.send_message("❌ Entre 1 et 100 messages.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=nombre)
    await interaction.followup.send(f"🧹 **{len(deleted)}** messages supprimés.", ephemeral=True)
    log_embed = discord.Embed(title="🧹 Clear", description=f"{len(deleted)} messages supprimés dans {interaction.channel.mention} par {interaction.user.mention}", color=GRAY, timestamp=datetime.datetime.utcnow())
    await log(interaction.guild, log_embed)

@bot.tree.command(name="lock", description="🔒 Verrouiller un salon")
@app_commands.describe(raison="Raison du lock")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction, raison: str = "Salon verrouillé"):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    embed = discord.Embed(title="🔒 Salon verrouillé", description=f"**Salon :** {interaction.channel.mention}\n**Raison :** {raison}\n**Par :** {interaction.user.mention}", color=RED, timestamp=datetime.datetime.utcnow())
    await interaction.response.send_message(embed=embed)
    await log(interaction.guild, embed)

@bot.tree.command(name="unlock", description="🔓 Déverrouiller un salon")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    embed = discord.Embed(title="🔓 Salon déverrouillé", description=f"**Salon :** {interaction.channel.mention}\n**Par :** {interaction.user.mention}", color=GREEN, timestamp=datetime.datetime.utcnow())
    await interaction.response.send_message(embed=embed)
    await log(interaction.guild, embed)

@bot.tree.command(name="slowmode", description="🐢 Définir le slowmode d'un salon")
@app_commands.describe(secondes="Délai en secondes (0 pour désactiver)")
@app_commands.checks.has_permissions(manage_channels=True)
async def slowmode(interaction: discord.Interaction, secondes: int):
    await interaction.channel.edit(slowmode_delay=secondes)
    if secondes == 0:
        await interaction.response.send_message("✅ Slowmode **désactivé**.", ephemeral=True)
    else:
        await interaction.response.send_message(f"🐢 Slowmode défini à **{secondes}s**.", ephemeral=True)

# ══════════════════════════════════════════════════
#  GESTION DES RÔLES
# ══════════════════════════════════════════════════
@bot.tree.command(name="role", description="🎭 Donner ou retirer un rôle à un membre")
@app_commands.describe(membre="Membre", role="Rôle à donner/retirer", action="add ou remove")
@app_commands.checks.has_permissions(manage_roles=True)
async def role(interaction: discord.Interaction, membre: discord.Member, role: discord.Role, action: str = "add"):
    if action == "add":
        await membre.add_roles(role)
        embed = discord.Embed(title="🎭 Rôle ajouté", description=f"{role.mention} → {membre.mention}", color=GREEN, timestamp=datetime.datetime.utcnow())
    else:
        await membre.remove_roles(role)
        embed = discord.Embed(title="🎭 Rôle retiré", description=f"{role.mention} ✗ {membre.mention}", color=ORANGE, timestamp=datetime.datetime.utcnow())
    await interaction.response.send_message(embed=embed)
    await log(interaction.guild, embed)

# ══════════════════════════════════════════════════
#  REACTION ROLES
# ══════════════════════════════════════════════════
@bot.tree.command(name="reactionrole", description="🎨 Créer un message de reaction roles")
@app_commands.describe(
    titre="Titre du message",
    description="Description du message",
    emoji1="Emoji 1", role1="Rôle pour emoji 1",
    emoji2="Emoji 2 (optionnel)", role2="Rôle pour emoji 2 (optionnel)",
    emoji3="Emoji 3 (optionnel)", role3="Rôle pour emoji 3 (optionnel)"
)
@app_commands.checks.has_permissions(manage_roles=True)
async def reactionrole(
    interaction: discord.Interaction,
    titre: str, description: str,
    emoji1: str, role1: discord.Role,
    emoji2: str = None, role2: discord.Role = None,
    emoji3: str = None, role3: discord.Role = None
):
    pairs = [(emoji1, role1)]
    if emoji2 and role2: pairs.append((emoji2, role2))
    if emoji3 and role3: pairs.append((emoji3, role3))

    desc = description + "\n\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for emoji, r in pairs:
        desc += f"{emoji} → {r.mention}\n"

    embed = discord.Embed(title=f"🎨 {titre}", description=desc, color=BLUE)
    embed.set_footer(text="Razy HUB • Réagis pour obtenir un rôle !")
    embed.timestamp = datetime.datetime.utcnow()

    await interaction.response.send_message("✅ Message de reaction roles créé !", ephemeral=True)
    msg = await interaction.channel.send(embed=embed)

    reaction_roles[msg.id] = {}
    for emoji, r in pairs:
        reaction_roles[msg.id][emoji] = r.id
        await msg.add_reaction(emoji)

# ══════════════════════════════════════════════════
#  INFOS MEMBRE / SERVEUR
# ══════════════════════════════════════════════════
@bot.tree.command(name="userinfo", description="👤 Infos sur un membre")
@app_commands.describe(membre="Membre (toi par défaut)")
async def userinfo(interaction: discord.Interaction, membre: discord.Member = None):
    m = membre or interaction.user
    roles = [r.mention for r in m.roles if r.name != "@everyone"]
    embed = discord.Embed(title=f"👤 {m.display_name}", color=m.color, timestamp=datetime.datetime.utcnow())
    embed.set_thumbnail(url=m.display_avatar.url)
    embed.add_field(name="🆔 ID", value=m.id, inline=True)
    embed.add_field(name="📅 Compte créé", value=m.created_at.strftime("%d/%m/%Y"), inline=True)
    embed.add_field(name="📥 A rejoint", value=m.joined_at.strftime("%d/%m/%Y"), inline=True)
    embed.add_field(name=f"🎭 Rôles ({len(roles)})", value=" ".join(roles) if roles else "Aucun", inline=False)
    embed.set_footer(text="Razy HUB • Scripts Premium")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="serverinfo", description="🏠 Infos sur le serveur")
async def serverinfo(interaction: discord.Interaction):
    g = interaction.guild
    embed = discord.Embed(title=f"🏠 {g.name}", color=RED, timestamp=datetime.datetime.utcnow())
    if g.icon: embed.set_thumbnail(url=g.icon.url)
    embed.add_field(name="👥 Membres", value=g.member_count, inline=True)
    embed.add_field(name="💬 Salons", value=len(g.text_channels), inline=True)
    embed.add_field(name="🔊 Vocaux", value=len(g.voice_channels), inline=True)
    embed.add_field(name="🎭 Rôles", value=len(g.roles), inline=True)
    embed.add_field(name="👑 Owner", value=g.owner.mention, inline=True)
    embed.add_field(name="📅 Créé le", value=g.created_at.strftime("%d/%m/%Y"), inline=True)
    embed.set_footer(text="Razy HUB • Scripts Premium")
    await interaction.response.send_message(embed=embed)

# ══════════════════════════════════════════════════
#  ERROR HANDLER
# ══════════════════════════════════════════════════
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Tu n'as pas les permissions nécessaires.", ephemeral=True)
    else:
        try:
            await interaction.response.send_message(f"❌ Erreur : `{error}`", ephemeral=True)
        except:
            pass
        print(f"Erreur commande: {error}")

bot.run(TOKEN)
