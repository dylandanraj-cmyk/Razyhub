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
    """Supprime TOUT — channels, catégories, rôles."""
    tasks = [ch.delete() for ch in guild.channels]
    await asyncio.gather(*tasks, return_exceptions=True)
    for role in guild.roles:
        if role.name != "@everyone" and not role.managed:
            try:
                await role.delete()
            except:
                pass

async def create_roles(guild):
    owner  = await guild.create_role(name="👑 Owner",  color=discord.Color.from_rgb(255, 215, 0),  hoist=True, permissions=discord.Permissions.all())
    admin  = await guild.create_role(name="⚡ Admin",   color=discord.Color.from_rgb(220, 20,  60), hoist=True, permissions=discord.Permissions(administrator=True))
    staff  = await guild.create_role(name="🛡️ Staff",  color=discord.Color.from_rgb(255, 140, 0),  hoist=True, permissions=discord.Permissions(manage_messages=True, kick_members=True, mute_members=True, read_messages=True, send_messages=True))
    vip    = await guild.create_role(name="💎 VIP",     color=discord.Color.from_rgb(0, 191, 255),  hoist=True, permissions=discord.Permissions(read_messages=True, send_messages=True))
    member = await guild.create_role(name="👤 Membre",  color=discord.Color.from_rgb(150, 150, 150),hoist=True, permissions=discord.Permissions(read_messages=True, send_messages=True, add_reactions=True))
    return owner, admin, staff, vip, member

def P(ev):  # public lecture seule
    return {ev: discord.PermissionOverwrite(read_messages=True, send_messages=False)}

def M(ev, member, vip, staff, admin, owner):  # membres peuvent écrire
    return {
        ev: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        vip:    discord.PermissionOverwrite(read_messages=True, send_messages=True),
        staff:  discord.PermissionOverwrite(read_messages=True, send_messages=True),
        admin:  discord.PermissionOverwrite(read_messages=True, send_messages=True),
        owner:  discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }

def S(ev, staff, admin, owner):  # staff seulement
    return {
        ev:    discord.PermissionOverwrite(read_messages=False),
        staff: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        admin: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        owner: discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }

async def build_server(guild, user):
    # 1. Tout supprimer
    await delete_all(guild)

    # 2. Rôles
    r_owner, r_admin, r_staff, r_vip, r_member = await create_roles(guild)
    ev = guild.default_role

    pub  = P(ev)
    chat = M(ev, r_member, r_vip, r_staff, r_admin, r_owner)
    staf = S(ev, r_staff, r_admin, r_owner)
    hide = {ev: discord.PermissionOverwrite(read_messages=False)}

    # ── MAIN ──
    cat_main = await guild.create_category("Main", overwrites={ev: discord.PermissionOverwrite(read_messages=True)})
    ch_news     = await guild.create_text_channel("📢・news",            category=cat_main, overwrites=pub)
    ch_purchase = await guild.create_text_channel("🟩・purchase",        category=cat_main, overwrites=pub)
    ch_pix      = await guild.create_text_channel("🟩・comprar-pix",     category=cat_main, overwrites=pub)
    ch_pay      = await guild.create_text_channel("🐴・razy-pay",        category=cat_main, overwrites=pub)
    ch_panel    = await guild.create_text_channel("💎・buy-admin-panel", category=cat_main, overwrites=pub)

    # ── HUB ──
    cat_hub = await guild.create_category("Hub", overwrites={ev: discord.PermissionOverwrite(read_messages=True)})
    await guild.create_text_channel("⚙️・executors", category=cat_hub, overwrites=pub)
    await guild.create_text_channel("👥・steals",    category=cat_hub, overwrites=pub)

    # ── SCRIPTS ── (que razy-hub + showcase)
    cat_scripts = await guild.create_category("Scripts", overwrites={ev: discord.PermissionOverwrite(read_messages=True)})
    ch_razy = await guild.create_text_channel("🟢・razy-hub",  category=cat_scripts, overwrites=pub)
    ch_show = await guild.create_text_channel("📸・showcase",   category=cat_scripts, overwrites=chat)
    ch_proof= await guild.create_text_channel("✅・proofs",     category=cat_scripts, overwrites=chat)

    # ── LOUNGE ──
    cat_lounge = await guild.create_category("Lounge", overwrites={ev: discord.PermissionOverwrite(read_messages=False)})
    ch_welcome = await guild.create_text_channel("🌴・welcome", category=cat_lounge, overwrites=pub)
    ch_chat    = await guild.create_text_channel("☁️・chat",    category=cat_lounge, overwrites=chat)
    await guild.create_voice_channel("📞・vc",   category=cat_lounge)
    await guild.create_voice_channel("RazyHUB", category=cat_lounge)

    # ── SUPPORT ──
    cat_sup = await guild.create_category("Support", overwrites={ev: discord.PermissionOverwrite(read_messages=False)})
    await guild.create_text_channel("🎫・tickets", category=cat_sup, overwrites=chat)
    await guild.create_text_channel("❓・faq",     category=cat_sup, overwrites=pub)

    # ── STAFF ──
    cat_stf = await guild.create_category("Staff", overwrites=hide)
    await guild.create_text_channel("📋・général",   category=cat_stf, overwrites=staf)
    await guild.create_text_channel("📊・logs",      category=cat_stf, overwrites=staf)
    await guild.create_text_channel("🚨・sanctions", category=cat_stf, overwrites=staf)
    await guild.create_voice_channel("🛡️ Staff VC",  category=cat_stf, overwrites=staf)

    # ── EMBEDS ──
    await ch_news.send(embed=discord.Embed(
        title="📢 Razy HUB — News",
        description="Bienvenue sur **Razy HUB** !\nToutes les annonces officielles ici.",
        color=discord.Color.from_rgb(255, 60, 60)
    ).set_footer(text="Razy HUB • Scripts Premium"))

    await ch_welcome.send(embed=discord.Embed(
        title="🌴 Bienvenue sur Razy HUB !",
        description=(
            "Le serveur officiel de **Razy HUB** — Scripts Roblox premium.\n\n"
            "🟢 **Notre script :** `razy-hub`\n\n"
            "🛒 **Acheter →** `#purchase`\n"
            "🎫 **Support →** `#tickets`\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ Bon jeu !"
        ),
        color=discord.Color.from_rgb(255, 60, 60)
    ).set_footer(text="Razy HUB • Scripts Premium"))

    await ch_purchase.send(embed=discord.Embed(
        title="🛒 Nos offres — Razy HUB",
        description=(
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔥 **Pack Starter** — X€\n"
            "> Accès Razy HUB de base\n\n"
            "💎 **Pack Premium** — X€\n"
            "> Accès complet + mises à jour\n\n"
            "👑 **Pack VIP** — X€\n"
            "> Tout inclus + support prioritaire\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📩 Ouvre un ticket pour acheter !"
        ),
        color=discord.Color.from_rgb(255, 215, 0)
    ).set_footer(text="Razy HUB • Scripts Premium"))

    await ch_razy.send(embed=discord.Embed(
        title="🟢 Razy HUB",
        description=(
            "Le script officiel **Razy HUB**.\n\n"
            "> Toutes les infos, loadstring et mises à jour ici.\n\n"
            "📥 Achète dans `#purchase` pour y accéder."
        ),
        color=discord.Color.green()
    ).set_footer(text="Razy HUB • Scripts Premium"))

    # Rôle Owner
    try:
        await user.add_roles(r_owner, r_admin)
    except:
        pass


@bot.tree.command(name="setup", description="🚀 Génère le serveur Razy HUB")
@app_commands.checks.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        await build_server(interaction.guild, interaction.user)
        await interaction.followup.send("✅ **Serveur Razy HUB généré !** 👑 Rôle Owner assigné.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Erreur : `{e}`", ephemeral=True)
        print(f"Erreur: {e}")


@bot.tree.command(name="reset", description="🔄 Reset COMPLET — supprime tout et recrée le serveur")
@app_commands.checks.has_permissions(administrator=True)
async def reset(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        await build_server(interaction.guild, interaction.user)
        await interaction.followup.send("🔄 **Reset terminé !** Tout supprimé et recréé. 👑 Rôle Owner réassigné.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Erreur : `{e}`", ephemeral=True)
        print(f"Erreur: {e}")


@setup.error
@reset.error
async def perm_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Tu dois être **Administrateur**.", ephemeral=True)


bot.run(TOKEN)
