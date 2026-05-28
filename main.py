import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import os
import datetime
import json
import re
import sqlite3
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ══════════════════════════════════════════════════
#  INTENTS & BOT
# ══════════════════════════════════════════════════
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ══════════════════════════════════════════════════
#  COULEURS
# ══════════════════════════════════════════════════
RED    = discord.Color.from_rgb(255, 60, 60)
GOLD   = discord.Color.from_rgb(255, 215, 0)
GREEN  = discord.Color.from_rgb(50, 205, 50)
BLUE   = discord.Color.from_rgb(0, 191, 255)
ORANGE = discord.Color.from_rgb(255, 140, 0)
GRAY   = discord.Color.from_rgb(100, 100, 100)
PURPLE = discord.Color.from_rgb(147, 51, 234)

# ══════════════════════════════════════════════════
#  DATABASE SQLite
# ══════════════════════════════════════════════════
def init_db():
    conn = sqlite3.connect("razy.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS warns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER,
        user_id INTEGER,
        moderator_id INTEGER,
        reason TEXT,
        timestamp TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS antilink (
        guild_id INTEGER PRIMARY KEY,
        enabled INTEGER DEFAULT 0,
        whitelist_roles TEXT DEFAULT '[]',
        whitelist_channels TEXT DEFAULT '[]',
        action TEXT DEFAULT 'delete',
        log_channel INTEGER DEFAULT NULL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS tickets (
        ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER,
        channel_id INTEGER,
        user_id INTEGER,
        status TEXT DEFAULT 'open',
        subject TEXT,
        created_at TEXT,
        closed_at TEXT DEFAULT NULL,
        claimed_by INTEGER DEFAULT NULL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS ticket_config (
        guild_id INTEGER PRIMARY KEY,
        category_id INTEGER DEFAULT NULL,
        log_channel INTEGER DEFAULT NULL,
        support_role INTEGER DEFAULT NULL,
        panel_message_id INTEGER DEFAULT NULL,
        panel_channel_id INTEGER DEFAULT NULL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS reaction_roles (
        message_id INTEGER,
        emoji TEXT,
        role_id INTEGER,
        guild_id INTEGER,
        PRIMARY KEY (message_id, emoji)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS automod (
        guild_id INTEGER PRIMARY KEY,
        anti_spam INTEGER DEFAULT 0,
        anti_caps INTEGER DEFAULT 0,
        caps_threshold INTEGER DEFAULT 70,
        spam_threshold INTEGER DEFAULT 5,
        spam_interval INTEGER DEFAULT 5,
        anti_mention INTEGER DEFAULT 0,
        mention_threshold INTEGER DEFAULT 5
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS leveling (
        guild_id INTEGER,
        user_id INTEGER,
        xp INTEGER DEFAULT 0,
        level INTEGER DEFAULT 0,
        messages INTEGER DEFAULT 0,
        PRIMARY KEY (guild_id, user_id)
    )""")
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect("razy.db")
    conn.row_factory = sqlite3.Row
    return conn

# ══════════════════════════════════════════════════
#  SPAM TRACKER (en mémoire)
# ══════════════════════════════════════════════════
spam_tracker = {}  # {user_id: [timestamps]}

# ══════════════════════════════════════════════════
#  CHARGEMENT DES COGS
# ══════════════════════════════════════════════════
async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"✅ Cog chargé: {filename}")
            except Exception as e:
                print(f"❌ Erreur cog {filename}: {e}")

# ══════════════════════════════════════════════════
#  ON READY
# ══════════════════════════════════════════════════
@bot.event
async def on_ready():
    init_db()
    print(f"✅ {bot.user} connecté!")
    print(f"📊 {len(bot.guilds)} serveur(s) | {sum(g.member_count for g in bot.guilds)} membres")
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="Razy HUB 🚀"),
        status=discord.Status.online
    )
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} commandes synchronisées")
    except Exception as e:
        print(f"❌ Erreur sync: {e}")

# ══════════════════════════════════════════════════
#  HELPERS GLOBAUX
# ══════════════════════════════════════════════════
async def send_log(guild: discord.Guild, embed: discord.Embed):
    db = get_db()
    try:
        row = db.execute("SELECT log_channel FROM ticket_config WHERE guild_id=?", (guild.id,)).fetchone()
        log_ch_id = row["log_channel"] if row and row["log_channel"] else None
    finally:
        db.close()

    channel = None
    if log_ch_id:
        channel = guild.get_channel(log_ch_id)
    if not channel:
        for ch in guild.text_channels:
            if any(x in ch.name.lower() for x in ["logs", "log", "journal"]):
                channel = ch
                break
    if channel:
        try:
            await channel.send(embed=embed)
        except:
            pass

async def get_or_create_muted_role(guild: discord.Guild) -> discord.Role:
    role = discord.utils.get(guild.roles, name="🔇 Muted")
    if not role:
        role = await guild.create_role(name="🔇 Muted", color=GRAY, reason="AutoCreate Muted role")
        for channel in guild.channels:
            try:
                await channel.set_permissions(role, send_messages=False, speak=False, add_reactions=False)
            except:
                pass
    return role

# ══════════════════════════════════════════════════
#  AUTOMOD — ON MESSAGE
# ══════════════════════════════════════════════════
LINK_PATTERN = re.compile(
    r"(https?://|discord\.gg/|discord\.com/invite/|bit\.ly/|tinyurl\.com/|t\.co/|"
    r"www\.|\.com|\.net|\.gg|\.io|\.xyz|\.tk|\.cf|\.ml)",
    re.IGNORECASE
)

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    db = get_db()
    try:
        # ── Anti-link ──
        al = db.execute("SELECT * FROM antilink WHERE guild_id=?", (message.guild.id,)).fetchone()
        if al and al["enabled"]:
            whitelist_roles = json.loads(al["whitelist_roles"])
            whitelist_channels = json.loads(al["whitelist_channels"])
            member = message.author

            user_role_ids = [r.id for r in member.roles]
            is_whitelisted_role = any(r in whitelist_roles for r in user_role_ids)
            is_whitelisted_channel = message.channel.id in whitelist_channels
            has_admin = member.guild_permissions.administrator

            if not (is_whitelisted_role or is_whitelisted_channel or has_admin):
                if LINK_PATTERN.search(message.content):
                    await message.delete()
                    action = al["action"]
                    warn_msg = await message.channel.send(
                        embed=discord.Embed(
                            title="🔗 Lien interdit",
                            description=f"{member.mention} Les liens ne sont pas autorisés ici !",
                            color=RED
                        ),
                        delete_after=5
                    )
                    if action in ("warn", "mute", "kick", "ban"):
                        # Enregistre le warn
                        db.execute(
                            "INSERT INTO warns (guild_id, user_id, moderator_id, reason, timestamp) VALUES (?,?,?,?,?)",
                            (message.guild.id, member.id, bot.user.id, "Anti-link auto", datetime.datetime.utcnow().isoformat())
                        )
                        db.commit()
                        warn_count = db.execute(
                            "SELECT COUNT(*) as c FROM warns WHERE guild_id=? AND user_id=?",
                            (message.guild.id, member.id)
                        ).fetchone()["c"]

                    if action == "mute":
                        muted = await get_or_create_muted_role(message.guild)
                        await member.add_roles(muted, reason="Anti-link")
                    elif action == "kick":
                        await member.kick(reason="Anti-link")
                    elif action == "ban":
                        await member.ban(reason="Anti-link")

                    log_embed = discord.Embed(
                        title="🔗 Anti-lien déclenché",
                        description=f"**Membre :** {member.mention}\n**Message :** {message.content[:100]}\n**Action :** `{action}`\n**Salon :** {message.channel.mention}",
                        color=RED, timestamp=datetime.datetime.utcnow()
                    )
                    await send_log(message.guild, log_embed)
                    return

        # ── Anti-spam ──
        am = db.execute("SELECT * FROM automod WHERE guild_id=?", (message.guild.id,)).fetchone()
        if am:
            member = message.author
            if not member.guild_permissions.administrator:
                now = datetime.datetime.utcnow().timestamp()
                uid = member.id
                if am["anti_spam"]:
                    if uid not in spam_tracker:
                        spam_tracker[uid] = []
                    spam_tracker[uid] = [t for t in spam_tracker[uid] if now - t < am["spam_interval"]]
                    spam_tracker[uid].append(now)
                    if len(spam_tracker[uid]) >= am["spam_threshold"]:
                        spam_tracker[uid] = []
                        await message.channel.purge(limit=am["spam_threshold"], check=lambda m: m.author == member)
                        muted = await get_or_create_muted_role(message.guild)
                        until = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
                        try:
                            await member.timeout(until, reason="Anti-spam auto")
                        except:
                            await member.add_roles(muted)
                        await message.channel.send(
                            embed=discord.Embed(title="🚫 Anti-Spam", description=f"{member.mention} a été mute 5 min pour spam.", color=RED),
                            delete_after=8
                        )
                        log_embed = discord.Embed(title="🚫 Anti-Spam", description=f"**Membre :** {member.mention}\n**Action :** Mute 5 min", color=ORANGE, timestamp=datetime.datetime.utcnow())
                        await send_log(message.guild, log_embed)
                        return

                if am["anti_caps"] and len(message.content) > 10:
                    caps = sum(1 for c in message.content if c.isupper())
                    ratio = (caps / len(message.content)) * 100
                    if ratio >= am["caps_threshold"]:
                        await message.delete()
                        await message.channel.send(
                            embed=discord.Embed(description=f"{member.mention} Évite les majuscules excessives !", color=ORANGE),
                            delete_after=4
                        )
                        return

                if am["anti_mention"]:
                    if len(message.mentions) >= am["mention_threshold"]:
                        await message.delete()
                        muted = await get_or_create_muted_role(message.guild)
                        await member.add_roles(muted, reason="Anti-mention spam")
                        await message.channel.send(
                            embed=discord.Embed(title="🚫 Anti-Mention", description=f"{member.mention} trop de mentions ! Mute appliqué.", color=RED),
                            delete_after=6
                        )
                        return

        # ── Leveling ──
        db.execute("""
            INSERT INTO leveling (guild_id, user_id, xp, level, messages) VALUES (?,?,?,?,?)
            ON CONFLICT(guild_id, user_id) DO UPDATE SET
            xp = xp + ?, messages = messages + 1
        """, (message.guild.id, message.author.id, 15, 0, 1, 15))
        row = db.execute("SELECT xp, level FROM leveling WHERE guild_id=? AND user_id=?", (message.guild.id, message.author.id)).fetchone()
        if row:
            xp, level = row["xp"], row["level"]
            xp_needed = (level + 1) * 100
            if xp >= xp_needed:
                new_level = level + 1
                db.execute("UPDATE leveling SET level=?, xp=0 WHERE guild_id=? AND user_id=?", (new_level, message.guild.id, message.author.id))
                try:
                    await message.channel.send(
                        embed=discord.Embed(
                            title="🎉 Level Up !",
                            description=f"{message.author.mention} a atteint le **niveau {new_level}** !",
                            color=GOLD
                        ),
                        delete_after=10
                    )
                except:
                    pass
        db.commit()

    finally:
        db.close()

    await bot.process_commands(message)

# ══════════════════════════════════════════════════
#  WELCOME / LEAVE
# ══════════════════════════════════════════════════
AUTO_ROLE_NAME = "👤 Membre"

@bot.event
async def on_member_join(member: discord.Member):
    guild = member.guild
    role = discord.utils.get(guild.roles, name=AUTO_ROLE_NAME)
    if role:
        try:
            await member.add_roles(role)
        except:
            pass

    channel = None
    for ch in guild.text_channels:
        if "welcome" in ch.name.lower() or "bienvenu" in ch.name.lower():
            channel = ch
            break

    if channel:
        embed = discord.Embed(
            title="🌴 Bienvenue sur Razy HUB !",
            description=(
                f"Salut {member.mention} ! Bienvenue sur **Razy HUB** 🚀\n\n"
                f"```\n"
                f"🎫  Ouvre un ticket pour acheter\n"
                f"📜  Lis le règlement\n"
                f"💬  Présente-toi !\n"
                f"```\n"
                f"Tu es le **{guild.member_count}ème** membre !"
            ),
            color=GREEN
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_image(url="https://i.imgur.com/your-banner.png")  # Remplace par ta bannière
        embed.set_footer(text="Razy HUB • Scripts Premium", icon_url=guild.icon.url if guild.icon else None)
        embed.timestamp = datetime.datetime.utcnow()
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member: discord.Member):
    guild = member.guild
    for ch in guild.text_channels:
        if "welcome" in ch.name.lower() or "bienvenu" in ch.name.lower():
            embed = discord.Embed(
                title="👋 Au revoir",
                description=f"**{member.name}** vient de quitter.\nNous sommes maintenant **{guild.member_count}** membres.",
                color=GRAY
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.timestamp = datetime.datetime.utcnow()
            await ch.send(embed=embed)
            break

# ══════════════════════════════════════════════════
#  REACTION ROLES EVENTS
# ══════════════════════════════════════════════════
@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.member and payload.member.bot:
        return
    db = get_db()
    try:
        row = db.execute(
            "SELECT role_id FROM reaction_roles WHERE message_id=? AND emoji=?",
            (payload.message_id, str(payload.emoji))
        ).fetchone()
        if row:
            guild = bot.get_guild(payload.guild_id)
            role = guild.get_role(row["role_id"])
            member = guild.get_member(payload.user_id)
            if role and member:
                await member.add_roles(role)
    finally:
        db.close()

@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    db = get_db()
    try:
        row = db.execute(
            "SELECT role_id FROM reaction_roles WHERE message_id=? AND emoji=?",
            (payload.message_id, str(payload.emoji))
        ).fetchone()
        if row:
            guild = bot.get_guild(payload.guild_id)
            role = guild.get_role(row["role_id"])
            member = guild.get_member(payload.user_id)
            if role and member:
                await member.remove_roles(role)
    finally:
        db.close()

# ══════════════════════════════════════════════════
#  ERROR HANDLER
# ══════════════════════════════════════════════════
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Tu n'as pas les permissions nécessaires.", ephemeral=True)
    elif isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(f"⏳ Commande en cooldown. Réessaie dans **{error.retry_after:.1f}s**.", ephemeral=True)
    else:
        try:
            await interaction.response.send_message(f"❌ Erreur : `{error}`", ephemeral=True)
        except:
            pass
        print(f"❌ Erreur commande: {error}")

# ══════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════
async def main():
    os.makedirs("cogs", exist_ok=True)
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

asyncio.run(main())
