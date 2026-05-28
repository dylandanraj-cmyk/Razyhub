import discord
from discord.ext import commands
from discord import app_commands
import datetime
import sqlite3
import asyncio
import random

def get_db():
    conn = sqlite3.connect("razy.db")
    conn.row_factory = sqlite3.Row
    return conn

RED    = discord.Color.from_rgb(255, 60, 60)
GOLD   = discord.Color.from_rgb(255, 215, 0)
GREEN  = discord.Color.from_rgb(50, 205, 50)
BLUE   = discord.Color.from_rgb(0, 191, 255)
ORANGE = discord.Color.from_rgb(255, 140, 0)
GRAY   = discord.Color.from_rgb(100, 100, 100)
PURPLE = discord.Color.from_rgb(147, 51, 234)


class UtilityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.giveaways = {}  # {message_id: {data}}

    # ══════════════════════════════════════════════
    #  LEVELING
    # ══════════════════════════════════════════════
    @app_commands.command(name="level", description="📊 Voir ton niveau")
    @app_commands.describe(membre="Membre (toi par défaut)")
    async def level(self, interaction: discord.Interaction, membre: discord.Member = None):
        m = membre or interaction.user
        db = get_db()
        try:
            row = db.execute("SELECT * FROM leveling WHERE guild_id=? AND user_id=?", (interaction.guild.id, m.id)).fetchone()
        finally:
            db.close()

        if not row:
            await interaction.response.send_message(f"ℹ️ {m.display_name} n'a pas encore de données.", ephemeral=True)
            return

        xp = row["xp"]
        level = row["level"]
        xp_needed = (level + 1) * 100
        progress = int((xp / xp_needed) * 20)
        bar = "█" * progress + "░" * (20 - progress)

        embed = discord.Embed(title=f"📊 Niveau de {m.display_name}", color=GOLD, timestamp=datetime.datetime.utcnow())
        embed.set_thumbnail(url=m.display_avatar.url)
        embed.add_field(name="🏆 Niveau", value=f"`{level}`", inline=True)
        embed.add_field(name="✨ XP", value=f"`{xp}` / `{xp_needed}`", inline=True)
        embed.add_field(name="💬 Messages", value=f"`{row['messages']}`", inline=True)
        embed.add_field(name="📈 Progression", value=f"`[{bar}]` {int((xp/xp_needed)*100)}%", inline=False)
        embed.set_footer(text="Razy HUB • +15 XP par message")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="🏆 Classement XP du serveur")
    async def leaderboard(self, interaction: discord.Interaction):
        db = get_db()
        try:
            rows = db.execute(
                "SELECT user_id, level, xp, messages FROM leveling WHERE guild_id=? ORDER BY level DESC, xp DESC LIMIT 10",
                (interaction.guild.id,)
            ).fetchall()
        finally:
            db.close()

        if not rows:
            await interaction.response.send_message("❌ Aucune donnée disponible.", ephemeral=True)
            return

        medals = ["🥇", "🥈", "🥉"]
        embed = discord.Embed(title="🏆 Classement — Razy HUB", color=GOLD, timestamp=datetime.datetime.utcnow())
        desc = ""
        for i, row in enumerate(rows):
            member = interaction.guild.get_member(row["user_id"])
            name = member.display_name if member else f"Inconnu ({row['user_id']})"
            medal = medals[i] if i < 3 else f"`#{i+1}`"
            desc += f"{medal} **{name}** — Niveau `{row['level']}` | XP `{row['xp']}` | Messages `{row['messages']}`\n"
        embed.description = desc
        embed.set_footer(text="Razy HUB • Classement XP")
        await interaction.response.send_message(embed=embed)

    # ══════════════════════════════════════════════
    #  GIVEAWAY
    # ══════════════════════════════════════════════
    @app_commands.command(name="giveaway", description="🎉 Lancer un giveaway")
    @app_commands.describe(
        duree="Durée (ex: 10m, 1h, 1d)",
        gagnants="Nombre de gagnants",
        prix="Ce qu'on gagne",
        salon="Salon (actuel par défaut)"
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def giveaway(self, interaction: discord.Interaction, duree: str, gagnants: int, prix: str, salon: discord.TextChannel = None):
        multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        try:
            unit = duree[-1].lower()
            amount = int(duree[:-1])
            seconds = amount * multipliers.get(unit, 60)
        except:
            await interaction.response.send_message("❌ Format invalide. Ex: `10m`, `1h`, `2d`", ephemeral=True)
            return

        if seconds < 10:
            await interaction.response.send_message("❌ Minimum 10 secondes.", ephemeral=True)
            return

        ch = salon or interaction.channel
        end_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds)

        embed = discord.Embed(
            title="🎉 GIVEAWAY !",
            description=(
                f"**Prix :** {prix}\n\n"
                f"Réagis avec 🎉 pour participer !\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🏆 **{gagnants}** gagnant(s)\n"
                f"⏰ Fin : <t:{int(end_time.timestamp())}:R>\n"
                f"🎙️ Organisé par : {interaction.user.mention}"
            ),
            color=GOLD
        )
        embed.set_footer(text=f"Razy HUB • Fin le {end_time.strftime('%d/%m/%Y à %H:%M')} UTC")
        embed.timestamp = end_time

        await interaction.response.send_message("✅ Giveaway lancé !", ephemeral=True)
        msg = await ch.send(embed=embed)
        await msg.add_reaction("🎉")

        self.giveaways[msg.id] = {
            "channel_id": ch.id,
            "prix": prix,
            "gagnants": gagnants,
            "end_time": end_time,
            "host": interaction.user.id
        }

        await asyncio.sleep(seconds)
        await self.end_giveaway(msg.id, interaction.guild)

    async def end_giveaway(self, msg_id: int, guild: discord.Guild):
        if msg_id not in self.giveaways:
            return
        data = self.giveaways.pop(msg_id)
        ch = guild.get_channel(data["channel_id"])
        if not ch:
            return

        try:
            msg = await ch.fetch_message(msg_id)
        except:
            return

        reaction = discord.utils.get(msg.reactions, emoji="🎉")
        if not reaction:
            await ch.send("❌ Giveaway terminé — Aucun participant.")
            return

        participants = [u async for u in reaction.users() if not u.bot]
        if not participants:
            await ch.send("❌ Giveaway terminé — Aucun participant valide.")
            return

        nb_gagnants = min(data["gagnants"], len(participants))
        winners = random.sample(participants, nb_gagnants)
        winners_mention = " ".join(w.mention for w in winners)

        embed = discord.Embed(
            title="🎉 Giveaway terminé !",
            description=f"**Prix :** {data['prix']}\n\n🏆 **Gagnant(s) :** {winners_mention}\n\nFélicitations !",
            color=GREEN
        )
        embed.set_footer(text="Razy HUB • Giveaway")
        embed.timestamp = datetime.datetime.utcnow()
        await ch.send(content=winners_mention, embed=embed)

        # Edit le message original
        ended_embed = discord.Embed(
            title="🎉 GIVEAWAY TERMINÉ",
            description=f"**Prix :** {data['prix']}\n\n🏆 **Gagnant(s) :** {winners_mention}",
            color=GRAY
        )
        ended_embed.set_footer(text="Ce giveaway est terminé")
        try:
            await msg.edit(embed=ended_embed)
        except:
            pass

    @app_commands.command(name="giveaway-reroll", description="🔄 Reroll un giveaway")
    @app_commands.describe(message_id="ID du message de giveaway")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def giveaway_reroll(self, interaction: discord.Interaction, message_id: str):
        try:
            msg = await interaction.channel.fetch_message(int(message_id))
        except:
            await interaction.response.send_message("❌ Message introuvable.", ephemeral=True)
            return

        reaction = discord.utils.get(msg.reactions, emoji="🎉")
        if not reaction:
            await interaction.response.send_message("❌ Pas de réaction 🎉 trouvée.", ephemeral=True)
            return

        participants = [u async for u in reaction.users() if not u.bot]
        if not participants:
            await interaction.response.send_message("❌ Aucun participant.", ephemeral=True)
            return

        winner = random.choice(participants)
        await interaction.response.send_message(
            embed=discord.Embed(title="🔄 Nouveau gagnant !", description=f"🏆 {winner.mention} a été retiré !", color=GOLD)
        )

    # ══════════════════════════════════════════════
    #  UTILITAIRES
    # ══════════════════════════════════════════════
    @app_commands.command(name="ping", description="🏓 Latence du bot")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        color = GREEN if latency < 100 else ORANGE if latency < 200 else RED
        embed = discord.Embed(
            title="🏓 Pong !",
            description=f"**Latence :** `{latency}ms`\n**Statut :** {'🟢 Excellent' if latency < 100 else '🟡 Moyen' if latency < 200 else '🔴 Élevé'}",
            color=color
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="botinfo", description="🤖 Infos sur le bot")
    async def botinfo(self, interaction: discord.Interaction):
        guilds = len(self.bot.guilds)
        members = sum(g.member_count for g in self.bot.guilds)
        commands_count = len(self.bot.tree.get_commands())

        embed = discord.Embed(title="🤖 Razy HUB Bot", color=BLUE, timestamp=datetime.datetime.utcnow())
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.add_field(name="🏠 Serveurs", value=f"`{guilds}`", inline=True)
        embed.add_field(name="👥 Membres", value=f"`{members}`", inline=True)
        embed.add_field(name="⚡ Commandes", value=f"`{commands_count}`", inline=True)
        embed.add_field(name="🏓 Latence", value=f"`{round(self.bot.latency * 1000)}ms`", inline=True)
        embed.add_field(name="🐍 discord.py", value=f"`{discord.__version__}`", inline=True)
        embed.add_field(name="👑 Développeur", value="Razy HUB Team", inline=True)
        embed.set_footer(text="Razy HUB • Scripts Premium")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="embed", description="💬 Créer un embed personnalisé")
    @app_commands.describe(titre="Titre", description="Description", couleur="Couleur hex (ex: ff0000)", footer="Footer")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def embed_cmd(self, interaction: discord.Interaction, titre: str, description: str, couleur: str = "0091ff", footer: str = "Razy HUB"):
        try:
            color = discord.Color(int(couleur.strip("#"), 16))
        except:
            color = BLUE
        embed = discord.Embed(title=titre, description=description, color=color, timestamp=datetime.datetime.utcnow())
        embed.set_footer(text=footer)
        await interaction.response.send_message("✅ Embed envoyé !", ephemeral=True)
        await interaction.channel.send(embed=embed)

    @app_commands.command(name="poll", description="📊 Créer un sondage")
    @app_commands.describe(question="Question", option1="Option 1", option2="Option 2", option3="Option 3", option4="Option 4")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def poll(self, interaction: discord.Interaction, question: str, option1: str, option2: str, option3: str = None, option4: str = None):
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        options = [o for o in [option1, option2, option3, option4] if o]

        desc = f"**{question}**\n\n━━━━━━━━━━━━━━━━━━━━━━\n"
        for i, opt in enumerate(options):
            desc += f"{emojis[i]} {opt}\n"

        embed = discord.Embed(title="📊 Sondage", description=desc, color=BLUE, timestamp=datetime.datetime.utcnow())
        embed.set_footer(text=f"Sondage par {interaction.user.display_name} • Razy HUB")
        await interaction.response.send_message("✅ Sondage créé !", ephemeral=True)
        msg = await interaction.channel.send(embed=embed)
        for i in range(len(options)):
            await msg.add_reaction(emojis[i])

    @app_commands.command(name="say", description="💬 Faire dire quelque chose au bot")
    @app_commands.describe(message="Message", salon="Salon cible")
    @app_commands.checks.has_permissions(administrator=True)
    async def say(self, interaction: discord.Interaction, message: str, salon: discord.TextChannel = None):
        ch = salon or interaction.channel
        await interaction.response.send_message("✅ Envoyé !", ephemeral=True)
        await ch.send(message)

    @app_commands.command(name="help", description="❓ Liste des commandes")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="❓ Commandes — Razy HUB Bot",
            color=BLUE,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        embed.add_field(
            name="🎫 Tickets",
            value="`/ticket-panel` `/ticket-config` `/ticket-add` `/ticket-remove` `/ticket-list`",
            inline=False
        )
        embed.add_field(
            name="🔨 Modération",
            value="`/ban` `/unban` `/kick` `/mute` `/unmute` `/warn` `/warns` `/unwarn` `/clearwarns` `/banlist`",
            inline=False
        )
        embed.add_field(
            name="🧹 Gestion",
            value="`/clear` `/lock` `/unlock` `/slowmode` `/role` `/annonce` `/embed` `/say`",
            inline=False
        )
        embed.add_field(
            name="🛡️ AutoMod",
            value="`/antilink` `/antilink-whitelist` `/antilink-status` `/automod`",
            inline=False
        )
        embed.add_field(
            name="🎉 Events",
            value="`/giveaway` `/giveaway-reroll` `/poll` `/reactionrole`",
            inline=False
        )
        embed.add_field(
            name="📊 Stats",
            value="`/level` `/leaderboard` `/userinfo` `/serverinfo` `/avatar` `/ping` `/botinfo`",
            inline=False
        )
        embed.add_field(
            name="⚙️ Setup",
            value="`/setup` `/reset`",
            inline=False
        )
        embed.set_footer(text="Razy HUB • Scripts Premium")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(UtilityCog(bot))
