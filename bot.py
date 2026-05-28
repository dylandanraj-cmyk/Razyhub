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
    tasks = [ch.delete() for ch in guild.channels]
    await asyncio.gather(*tasks, return_exceptions=True)
    for role in guild.roles:
        if role.name != "@everyone" and not role.managed:
            try:
                await role.delete()
            except:
                pass

async def create_roles(guild):
    owner = await guild.create_role(name="👑 Owner",        color=discord.Color.from_rgb(255, 215, 0),  hoist=True, permissions=discord.Permissions.all())
    admin = await guild.create_role(name="⚡ Admin",         color=discord.Color.from_rgb(220, 20,  60), hoist=True, permissions=discord.Permissions(administrator=True))
    staff = await guild.create_role(name="🛡️ Staff",        color=discord.Color.from_rgb(255, 140, 0),  hoist=True, permissions=discord.Permissions(manage_messages=True, kick_members=True, mute_members=True, read_messages=True, send_messages=True))
    vip   = await guild.create_role(name="💎 VIP",           color=discord.Color.from_rgb(0,   191, 255), hoist=True, permissions=discord.Permissions(read_messages=True, send_messages=True))
    buyer = await guild.create_role(name="🛒 Acheteur",      color=discord.Color.from_rgb(50,  205, 50),  hoist=True, permissions=discord.Permissions(read_messages=True, send_messages=True))
    member= await guild.create_role(name="👤 Membre",        color=discord.Color.from_rgb(150, 150, 150), hoist=True, permissions=discord.Permissions(read_messages=True, send_messages=True, add_reactions=True))
    return owner, admin, staff, vip, buyer, member

def ow_public(everyone):
    return {everyone: discord.PermissionOverwrite(read_messages=True, send_messages=False)}

def ow_members(everyone, member, buyer, vip, staff, admin, owner):
    return {
        everyone: discord.PermissionOverwrite(read_messages=False),
        member:   discord.PermissionOverwrite(read_messages=True, send_messages=True),
        buyer:    discord.PermissionOverwrite(read_messages=True, send_messages=True),
        vip:      discord.PermissionOverwrite(read_messages=True, send_messages=True),
        staff:    discord.PermissionOverwrite(read_messages=True, send_messages=True),
        admin:    discord.PermissionOverwrite(read_messages=True, send_messages=True),
        owner:    discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }

def ow_buyer_only(everyone, buyer, vip, staff, admin, owner):
    return {
        everyone: discord.PermissionOverwrite(read_messages=False),
        buyer:    discord.PermissionOverwrite(read_messages=True, send_messages=True),
        vip:      discord.PermissionOverwrite(read_messages=True, send_messages=True),
        staff:    discord.PermissionOverwrite(read_messages=True, send_messages=True),
        admin:    discord.PermissionOverwrite(read_messages=True, send_messages=True),
        owner:    discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }

def ow_staff_only(everyone, staff, admin, owner):
    return {
        everyone: discord.PermissionOverwrite(read_messages=False),
        staff:    discord.PermissionOverwrite(read_messages=True, send_messages=True),
        admin:    discord.PermissionOverwrite(read_messages=True, send_messages=True),
        owner:    discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }

async def build_server(guild, interaction_user):
    # 1. Nettoyage
    await delete_all(guild)

    # 2. Rôles
    r_owner, r_admin, r_staff, r_vip, r_buyer, r_member = await create_roles(guild)
    ev = guild.default_role

    pub   = ow_public(ev)
    mem   = ow_members(ev, r_member, r_buyer, r_vip, r_staff, r_admin, r_owner)
    buy   = ow_buyer_only(ev, r_buyer, r_vip, r_staff, r_admin, r_owner)
    stf   = ow_staff_only(ev, r_staff, r_admin, r_owner)
    hidden= {ev: discord.PermissionOverwrite(read_messages=False)}

    # ── MAIN ──
    cat_main = await guild.create_category("Main", overwrites={ev: discord.PermissionOverwrite(read_messages=True)})
    ch_news    = await guild.create_text_channel("📢・news",          category=cat_main, overwrites=pub)
    ch_buy_info= await guild.create_text_channel("🟩・purchase",      category=cat_main, overwrites=pub)
    ch_pix     = await guild.create_text_channel("🟩・comprar-pix",   category=cat_main, overwrites=pub)
    ch_pay     = await guild.create_text_channel("🐴・razy-pay",      category=cat_main, overwrites=pub)
    ch_panel   = await guild.create_text_channel("💎・buy-admin-panel",category=cat_main, overwrites=pub)

    # ── HUB ──
    cat_hub = await guild.create_category("Hub", overwrites={ev: discord.PermissionOverwrite(read_messages=True)})
    ch_exec  = await guild.create_text_channel("⚙️・executors",       category=cat_hub, overwrites=pub)
    ch_steals= await guild.create_text_channel("👥・steals",           category=cat_hub, overwrites=pub)

    # ── SCRIPTS ──
    cat_scripts = await guild.create_category("Scripts", overwrites={ev: discord.PermissionOverwrite(read_messages=True)})
    ch_razy     = await guild.create_text_channel("🟢・razy-hub",      category=cat_scripts, overwrites=pub)
    ch_pvp      = await guild.create_text_channel("🟢・razyhub-pvp",   category=cat_scripts, overwrites=pub)
    ch_scam     = await guild.create_text_channel("🟢・razyhub-scam-tp",category=cat_scripts, overwrites=pub)
    ch_flash    = await guild.create_text_channel("🔴・razy-flash-tp", category=cat_scripts, overwrites=pub)

    # ── LOUNGE ──
    cat_lounge = await guild.create_category("Lounge", overwrites={ev: discord.PermissionOverwrite(read_messages=False)})
    ch_welcome = await guild.create_text_channel("🌴・welcome",        category=cat_lounge, overwrites=pub)
    ch_chat    = await guild.create_text_channel("☁️・chat",           category=cat_lounge, overwrites=mem)
    ch_br      = await guild.create_text_channel("🇧🇷・chat-brazil",   category=cat_lounge, overwrites=mem)
    ch_vc      = await guild.create_voice_channel("📞・vc",            category=cat_lounge)
    ch_razyhub = await guild.create_voice_channel("RazyHUB",          category=cat_lounge)

    # ── SHOWCASE ──
    cat_show = await guild.create_category("Showcase", overwrites={ev: discord.PermissionOverwrite(read_messages=True)})
    ch_show  = await guild.create_text_channel("📸・showcase",         category=cat_show, overwrites=pub)
    ch_proof = await guild.create_text_channel("✅・proofs",           category=cat_show, overwrites=pub)

    # ── ACHETEURS ──
    cat_vip = await guild.create_category("Acheteurs", overwrites=hidden)
    ch_dl   = await guild.create_text_channel("📥・téléchargements",   category=cat_vip, overwrites=buy)
    ch_key  = await guild.create_text_channel("🔑・licences",          category=cat_vip, overwrites=buy)
    ch_supp = await guild.create_text_channel("❓・support",           category=cat_vip, overwrites=buy)

    # ── SUPPORT ──
    cat_sup  = await guild.create_category("Support", overwrites={ev: discord.PermissionOverwrite(read_messages=False)})
    ch_ticket= await guild.create_text_channel("🎫・tickets",          category=cat_sup, overwrites=mem)
    ch_faq   = await guild.create_text_channel("❓・faq",              category=cat_sup, overwrites=pub)

    # ── STAFF ──
    cat_stf  = await guild.create_category("Staff", overwrites=hidden)
    await guild.create_text_channel("📋・général",   category=cat_stf, overwrites=stf)
    await guild.create_text_channel("📊・logs",      category=cat_stf, overwrites=stf)
    await guild.create_text_channel("🚨・sanctions", category=cat_stf, overwrites=stf)
    await guild.create_voice_channel("🛡️ Staff VC",  category=cat_stf, overwrites=stf)

    # ── MESSAGES ──
    embed_news = discord.Embed(
        title="📢 Razy HUB — News",
        description="Bienvenue sur **Razy HUB** !\nRetrouve ici toutes les annonces officielles.",
        color=discord.Color.from_rgb(255, 60, 60)
    )
    embed_news.set_footer(text="Razy HUB • Scripts Premium")
    await ch_news.send(embed=embed_news)

    embed_welcome = discord.Embed(
        title="🌴 Bienvenue sur Razy HUB !",
        description=(
            "Le serveur officiel de **Razy HUB** — Scripts Roblox premium.\n\n"
            "🟢 **Scripts disponibles :**\n"
            "> • Razy HUB | PVP | Scam-TP | Flash-TP\n\n"
            "🛒 **Acheter :** va dans `#purchase`\n"
            "🎫 **Support :** ouvre un ticket\n"
            "📜 **Règles :** respecte les membres\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ Bon jeu et bonne exploration !"
        ),
        color=discord.Color.from_rgb(255, 60, 60)
    )
    embed_welcome.set_footer(text="Razy HUB • Scripts Premium")
    await ch_welcome.send(embed=embed_welcome)

    embed_purchase = discord.Embed(
        title="🛒 Comment acheter ?",
        description=(
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔥 **Pack Starter** — X€\n"
            "> Accès Razy HUB de base\n\n"
            "💎 **Pack Premium** — X€\n"
            "> Tous les scripts + mises à jour\n\n"
            "👑 **Pack VIP** — X€\n"
            "> Tout inclus + support prioritaire\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📩 Ouvre un ticket pour acheter !"
        ),
        color=discord.Color.from_rgb(255, 215, 0)
    )
    embed_purchase.set_footer(text="Razy HUB • Scripts Premium")
    await ch_buy_info.send(embed=embed_purchase)

    # Rôle Owner à l'utilisateur
    try:
        await interaction_user.add_roles(r_owner, r_admin)
    except:
        pass


@bot.tree.command(name="setup", description="🚀 Génère le serveur Razy HUB complet")
@app_commands.checks.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        await build_server(interaction.guild, interaction.user)
        await interaction.followup.send(
            "✅ **Serveur Razy HUB généré !**\n"
            "Toutes les catégories, channels et rôles ont été créés.\n"
            "👑 Rôle Owner assigné.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(f"❌ Erreur : `{e}`", ephemeral=True)
        print(f"Erreur setup: {e}")


@bot.tree.command(name="reset", description="🔄 Reset complet du serveur Razy HUB")
@app_commands.checks.has_permissions(administrator=True)
async def reset(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        await build_server(interaction.guild, interaction.user)
        await interaction.followup.send(
            "🔄 **Serveur Razy HUB reset avec succès !**\n"
            "Tout a été supprimé et recréé proprement.\n"
            "👑 Rôle Owner réassigné.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(f"❌ Erreur : `{e}`", ephemeral=True)
        print(f"Erreur reset: {e}")


@setup.error
@reset.error
async def perm_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Tu dois être **Administrateur**.", ephemeral=True)


bot.run(TOKEN)
