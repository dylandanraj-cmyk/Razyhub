import discord
from discord.ext import commands
from discord import app_commands
import datetime
import sqlite3
import asyncio

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

async def send_log(guild, embed):
    for ch in guild.text_channels:
        if any(x in ch.name.lower() for x in ["logs", "log", "journal"]):
            try:
                await ch.send(embed=embed)
            except:
                pass
            break

async def get_or_create_muted_role(guild):
    role = discord.utils.get(guild.roles, name="🔇 Muted")
    if not role:
        role = await guild.create_role(name="🔇 Muted", color=GRAY, reason="AutoCreate")
        for channel in guild.channels:
            try:
                await channel.set_permissions(role, send_messages=False, speak=False, add_reactions=False)
            except:
                pass
    return role


class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ══════════════════════════════════════════════
    #  BAN / UNBAN
    # ══════════════════════════════════════════════
    @app_commands.command(name="ban", description="🔨 Bannir un membre")
    @app_commands.describe(membre="Membre à bannir", raison="Raison", delete_days="Supprimer messages (jours, 0-7)")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison fournie", delete_days: int = 0):
        if membre.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("❌ Tu ne peux pas bannir ce membre (rôle supérieur ou égal).", ephemeral=True)
            return
        if membre == interaction.guild.owner:
            await interaction.response.send_message("❌ Impossible de bannir le propriétaire.", ephemeral=True)
            return

        try:
            await membre.send(embed=discord.Embed(
                title="🔨 Tu as été banni",
                description=f"**Serveur :** {interaction.guild.name}\n**Raison :** {raison}\n**Par :** {interaction.user}",
                color=RED
            ))
        except:
            pass

        await membre.ban(reason=f"{interaction.user} | {raison}", delete_message_days=min(delete_days, 7))
        embed = discord.Embed(
            title="🔨 Membre banni",
            description=f"**Membre :** {membre} (`{membre.id}`)\n**Raison :** {raison}\n**Par :** {interaction.user.mention}\n**Messages sup. :** {delete_days}j",
            color=RED, timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url=membre.display_avatar.url)
        await interaction.response.send_message(embed=embed)
        await send_log(interaction.guild, embed)

    @app_commands.command(name="unban", description="✅ Débannir un utilisateur")
    @app_commands.describe(user_id="ID de l'utilisateur", raison="Raison")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str, raison: str = "Aucune raison"):
        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user, reason=raison)
            embed = discord.Embed(
                title="✅ Membre débanni",
                description=f"**Membre :** {user} (`{user_id}`)\n**Par :** {interaction.user.mention}\n**Raison :** {raison}",
                color=GREEN, timestamp=datetime.datetime.utcnow()
            )
            await interaction.response.send_message(embed=embed)
            await send_log(interaction.guild, embed)
        except discord.NotFound:
            await interaction.response.send_message("❌ Utilisateur non trouvé ou non banni.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur : `{e}`", ephemeral=True)

    @app_commands.command(name="banlist", description="📋 Liste des membres bannis")
    @app_commands.checks.has_permissions(ban_members=True)
    async def banlist(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        bans = [entry async for entry in interaction.guild.bans(limit=20)]
        if not bans:
            await interaction.followup.send("✅ Aucun membre banni.", ephemeral=True)
            return
        embed = discord.Embed(title=f"📋 Bannis ({len(bans)} affichés)", color=RED, timestamp=datetime.datetime.utcnow())
        for ban in bans:
            embed.add_field(name=f"{ban.user}", value=f"ID: `{ban.user.id}` | Raison: {ban.reason or 'Inconnue'}", inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ══════════════════════════════════════════════
    #  KICK
    # ══════════════════════════════════════════════
    @app_commands.command(name="kick", description="👢 Expulser un membre")
    @app_commands.describe(membre="Membre à kick", raison="Raison")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison fournie"):
        if membre.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("❌ Tu ne peux pas kick ce membre.", ephemeral=True)
            return
        try:
            await membre.send(embed=discord.Embed(
                title="👢 Tu as été expulsé",
                description=f"**Serveur :** {interaction.guild.name}\n**Raison :** {raison}",
                color=ORANGE
            ))
        except:
            pass
        await membre.kick(reason=f"{interaction.user} | {raison}")
        embed = discord.Embed(
            title="👢 Membre expulsé",
            description=f"**Membre :** {membre}\n**Raison :** {raison}\n**Par :** {interaction.user.mention}",
            color=ORANGE, timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url=membre.display_avatar.url)
        await interaction.response.send_message(embed=embed)
        await send_log(interaction.guild, embed)

    # ══════════════════════════════════════════════
    #  MUTE / UNMUTE (Timeout natif Discord)
    # ══════════════════════════════════════════════
    @app_commands.command(name="mute", description="🔇 Timeout un membre")
    @app_commands.describe(membre="Membre", duree="Durée (ex: 10m, 1h, 1d)", raison="Raison")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(self, interaction: discord.Interaction, membre: discord.Member, duree: str = "10m", raison: str = "Aucune raison"):
        if membre.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("❌ Tu ne peux pas mute ce membre.", ephemeral=True)
            return

        # Parse durée
        multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        try:
            unit = duree[-1].lower()
            amount = int(duree[:-1])
            seconds = amount * multipliers.get(unit, 60)
        except:
            await interaction.response.send_message("❌ Format invalide. Exemples: `10m`, `1h`, `2d`", ephemeral=True)
            return

        if seconds > 2419200:  # 28 jours max Discord
            await interaction.response.send_message("❌ Maximum 28 jours.", ephemeral=True)
            return

        until = datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds)
        await membre.timeout(until, reason=f"{interaction.user} | {raison}")

        try:
            await membre.send(embed=discord.Embed(
                title="🔇 Tu as été mute",
                description=f"**Serveur :** {interaction.guild.name}\n**Durée :** {duree}\n**Raison :** {raison}",
                color=ORANGE
            ))
        except:
            pass

        embed = discord.Embed(
            title="🔇 Membre mute",
            description=f"**Membre :** {membre.mention}\n**Durée :** `{duree}`\n**Raison :** {raison}\n**Par :** {interaction.user.mention}\n**Fin :** <t:{int(until.timestamp())}:R>",
            color=ORANGE, timestamp=datetime.datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed)
        await send_log(interaction.guild, embed)

    @app_commands.command(name="unmute", description="🔊 Retirer le mute d'un membre")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unmute(self, interaction: discord.Interaction, membre: discord.Member):
        await membre.timeout(None)
        embed = discord.Embed(
            title="🔊 Membre unmute",
            description=f"**Membre :** {membre.mention}\n**Par :** {interaction.user.mention}",
            color=GREEN, timestamp=datetime.datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed)
        await send_log(interaction.guild, embed)

    # ══════════════════════════════════════════════
    #  WARN SYSTEM
    # ══════════════════════════════════════════════
    @app_commands.command(name="warn", description="⚠️ Avertir un membre")
    @app_commands.describe(membre="Membre", raison="Raison")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warn(self, interaction: discord.Interaction, membre: discord.Member, raison: str):
        db = get_db()
        try:
            db.execute(
                "INSERT INTO warns (guild_id, user_id, moderator_id, reason, timestamp) VALUES (?,?,?,?,?)",
                (interaction.guild.id, membre.id, interaction.user.id, raison, datetime.datetime.utcnow().isoformat())
            )
            db.commit()
            count = db.execute(
                "SELECT COUNT(*) as c FROM warns WHERE guild_id=? AND user_id=?",
                (interaction.guild.id, membre.id)
            ).fetchone()["c"]
        finally:
            db.close()

        try:
            await membre.send(embed=discord.Embed(
                title="⚠️ Avertissement",
                description=f"**Serveur :** {interaction.guild.name}\n**Raison :** {raison}\n**Avertissement n°{count}**",
                color=ORANGE
            ))
        except:
            pass

        embed = discord.Embed(
            title="⚠️ Membre averti",
            description=f"**Membre :** {membre.mention}\n**Raison :** {raison}\n**Par :** {interaction.user.mention}\n**Total warns :** `{count}`",
            color=ORANGE, timestamp=datetime.datetime.utcnow()
        )

        # Auto-sanctions selon le nombre de warns
        if count >= 5:
            embed.add_field(name="🔨 Action auto", value="5 warns → Ban", inline=False)
            await membre.ban(reason=f"5 warns auto-ban")
        elif count >= 3:
            embed.add_field(name="🔇 Action auto", value="3 warns → Mute 1h", inline=False)
            until = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            await membre.timeout(until, reason="3 warns auto-mute")

        await interaction.response.send_message(embed=embed)
        await send_log(interaction.guild, embed)

    @app_commands.command(name="warns", description="📋 Voir les warns d'un membre")
    @app_commands.describe(membre="Membre (toi par défaut)")
    async def warns(self, interaction: discord.Interaction, membre: discord.Member = None):
        m = membre or interaction.user
        db = get_db()
        try:
            rows = db.execute(
                "SELECT * FROM warns WHERE guild_id=? AND user_id=? ORDER BY id DESC LIMIT 10",
                (interaction.guild.id, m.id)
            ).fetchall()
        finally:
            db.close()

        embed = discord.Embed(
            title=f"⚠️ Warns de {m.display_name}",
            description=f"**Total :** `{len(rows)}` avertissement(s)",
            color=ORANGE if rows else GREEN,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url=m.display_avatar.url)
        for row in rows:
            mod = interaction.guild.get_member(row["moderator_id"])
            embed.add_field(
                name=f"#{row['id']} — {row['timestamp'][:10]}",
                value=f"**Raison :** {row['reason']}\n**Par :** {mod.mention if mod else 'Inconnu'}",
                inline=False
            )
        if not rows:
            embed.description = "✅ Aucun avertissement !"
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="unwarn", description="🗑️ Supprimer un warn")
    @app_commands.describe(warn_id="ID du warn à supprimer")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def unwarn(self, interaction: discord.Interaction, warn_id: int):
        db = get_db()
        try:
            row = db.execute("SELECT * FROM warns WHERE id=? AND guild_id=?", (warn_id, interaction.guild.id)).fetchone()
            if not row:
                await interaction.response.send_message("❌ Warn introuvable.", ephemeral=True)
                return
            db.execute("DELETE FROM warns WHERE id=?", (warn_id,))
            db.commit()
        finally:
            db.close()
        await interaction.response.send_message(f"✅ Warn `#{warn_id}` supprimé.", ephemeral=True)

    @app_commands.command(name="clearwarns", description="🧹 Effacer tous les warns d'un membre")
    @app_commands.checks.has_permissions(administrator=True)
    async def clearwarns(self, interaction: discord.Interaction, membre: discord.Member):
        db = get_db()
        try:
            count = db.execute("SELECT COUNT(*) as c FROM warns WHERE guild_id=? AND user_id=?", (interaction.guild.id, membre.id)).fetchone()["c"]
            db.execute("DELETE FROM warns WHERE guild_id=? AND user_id=?", (interaction.guild.id, membre.id))
            db.commit()
        finally:
            db.close()
        await interaction.response.send_message(f"✅ **{count}** warn(s) supprimé(s) pour {membre.mention}.", ephemeral=True)

    # ══════════════════════════════════════════════
    #  CLEAR / PURGE
    # ══════════════════════════════════════════════
    @app_commands.command(name="clear", description="🧹 Supprimer des messages")
    @app_commands.describe(nombre="Nombre (1-100)", membre="Filtrer par membre (optionnel)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, nombre: int, membre: discord.Member = None):
        if not 1 <= nombre <= 100:
            await interaction.response.send_message("❌ Entre 1 et 100.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        check = (lambda m: m.author == membre) if membre else None
        deleted = await interaction.channel.purge(limit=nombre, check=check)
        await interaction.followup.send(f"🧹 **{len(deleted)}** messages supprimés.", ephemeral=True)
        log_embed = discord.Embed(
            title="🧹 Clear",
            description=f"**{len(deleted)}** messages dans {interaction.channel.mention}\n**Par :** {interaction.user.mention}{f' | Filtre: {membre}' if membre else ''}",
            color=GRAY, timestamp=datetime.datetime.utcnow()
        )
        await send_log(interaction.guild, log_embed)

    # ══════════════════════════════════════════════
    #  LOCK / UNLOCK / SLOWMODE
    # ══════════════════════════════════════════════
    @app_commands.command(name="lock", description="🔒 Verrouiller un salon")
    @app_commands.describe(salon="Salon (actuel par défaut)", raison="Raison")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock(self, interaction: discord.Interaction, salon: discord.TextChannel = None, raison: str = "Verrouillé par le staff"):
        ch = salon or interaction.channel
        await ch.set_permissions(interaction.guild.default_role, send_messages=False)
        embed = discord.Embed(
            title="🔒 Salon verrouillé",
            description=f"**Salon :** {ch.mention}\n**Raison :** {raison}\n**Par :** {interaction.user.mention}",
            color=RED, timestamp=datetime.datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed)
        await send_log(interaction.guild, embed)

    @app_commands.command(name="unlock", description="🔓 Déverrouiller un salon")
    @app_commands.describe(salon="Salon (actuel par défaut)")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock(self, interaction: discord.Interaction, salon: discord.TextChannel = None):
        ch = salon or interaction.channel
        await ch.set_permissions(interaction.guild.default_role, send_messages=True)
        embed = discord.Embed(
            title="🔓 Salon déverrouillé",
            description=f"**Salon :** {ch.mention}\n**Par :** {interaction.user.mention}",
            color=GREEN, timestamp=datetime.datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed)
        await send_log(interaction.guild, embed)

    @app_commands.command(name="slowmode", description="🐢 Slowmode d'un salon")
    @app_commands.describe(secondes="Délai (0 = désactivé)")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode(self, interaction: discord.Interaction, secondes: int):
        await interaction.channel.edit(slowmode_delay=max(0, min(secondes, 21600)))
        txt = "désactivé" if secondes == 0 else f"**{secondes}s**"
        await interaction.response.send_message(f"🐢 Slowmode → {txt}", ephemeral=True)

    # ══════════════════════════════════════════════
    #  ROLE
    # ══════════════════════════════════════════════
    @app_commands.command(name="role", description="🎭 Donner/retirer un rôle")
    @app_commands.describe(membre="Membre", role="Rôle", action="add ou remove")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def role(self, interaction: discord.Interaction, membre: discord.Member, role: discord.Role, action: str = "add"):
        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message("❌ Ce rôle est au-dessus de moi.", ephemeral=True)
            return
        if action == "add":
            await membre.add_roles(role, reason=f"Par {interaction.user}")
            embed = discord.Embed(title="🎭 Rôle ajouté", description=f"{role.mention} → {membre.mention}", color=GREEN, timestamp=datetime.datetime.utcnow())
        else:
            await membre.remove_roles(role, reason=f"Par {interaction.user}")
            embed = discord.Embed(title="🎭 Rôle retiré", description=f"{role.mention} ✗ {membre.mention}", color=ORANGE, timestamp=datetime.datetime.utcnow())
        await interaction.response.send_message(embed=embed)
        await send_log(interaction.guild, embed)

    # ══════════════════════════════════════════════
    #  INFOS
    # ══════════════════════════════════════════════
    @app_commands.command(name="userinfo", description="👤 Infos sur un membre")
    @app_commands.describe(membre="Membre (toi par défaut)")
    async def userinfo(self, interaction: discord.Interaction, membre: discord.Member = None):
        m = membre or interaction.user
        roles = [r.mention for r in reversed(m.roles) if r.name != "@everyone"]
        db = get_db()
        try:
            warn_count = db.execute("SELECT COUNT(*) as c FROM warns WHERE guild_id=? AND user_id=?", (interaction.guild.id, m.id)).fetchone()["c"]
            lv = db.execute("SELECT level, xp, messages FROM leveling WHERE guild_id=? AND user_id=?", (interaction.guild.id, m.id)).fetchone()
        finally:
            db.close()

        flags = []
        if m.guild_permissions.administrator: flags.append("👑 Admin")
        if m.guild_permissions.manage_guild: flags.append("⚙️ Manager")
        if m.bot: flags.append("🤖 Bot")
        if m.premium_since: flags.append("💎 Booster")

        embed = discord.Embed(title=f"👤 {m.display_name}", color=m.top_role.color, timestamp=datetime.datetime.utcnow())
        embed.set_thumbnail(url=m.display_avatar.url)
        embed.add_field(name="🆔 ID", value=f"`{m.id}`", inline=True)
        embed.add_field(name="📅 Compte créé", value=f"<t:{int(m.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="📥 A rejoint", value=f"<t:{int(m.joined_at.timestamp())}:R>", inline=True)
        embed.add_field(name="⚠️ Warns", value=f"`{warn_count}`", inline=True)
        embed.add_field(name="📊 Level", value=f"`{lv['level'] if lv else 0}` (XP: `{lv['xp'] if lv else 0}`)", inline=True)
        embed.add_field(name="💬 Messages", value=f"`{lv['messages'] if lv else 0}`", inline=True)
        if flags:
            embed.add_field(name="🏷️ Tags", value=" | ".join(flags), inline=False)
        embed.add_field(name=f"🎭 Rôles ({len(roles)})", value=" ".join(roles[:15]) + ("..." if len(roles) > 15 else "") if roles else "Aucun", inline=False)
        embed.set_footer(text="Razy HUB • Scripts Premium")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="serverinfo", description="🏠 Infos sur le serveur")
    async def serverinfo(self, interaction: discord.Interaction):
        g = interaction.guild
        bots = sum(1 for m in g.members if m.bot)
        humans = g.member_count - bots
        embed = discord.Embed(title=f"🏠 {g.name}", color=RED, timestamp=datetime.datetime.utcnow())
        if g.icon:
            embed.set_thumbnail(url=g.icon.url)
        if g.banner:
            embed.set_image(url=g.banner.url)
        embed.add_field(name="👥 Membres", value=f"`{g.member_count}` (👤{humans} / 🤖{bots})", inline=True)
        embed.add_field(name="💬 Salons texte", value=f"`{len(g.text_channels)}`", inline=True)
        embed.add_field(name="🔊 Salons vocaux", value=f"`{len(g.voice_channels)}`", inline=True)
        embed.add_field(name="🎭 Rôles", value=f"`{len(g.roles)}`", inline=True)
        embed.add_field(name="📁 Catégories", value=f"`{len(g.categories)}`", inline=True)
        embed.add_field(name="💎 Boosts", value=f"`{g.premium_subscription_count}` (Niveau {g.premium_tier})", inline=True)
        embed.add_field(name="👑 Owner", value=g.owner.mention, inline=True)
        embed.add_field(name="📅 Créé le", value=f"<t:{int(g.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="🌍 Région", value=str(g.preferred_locale), inline=True)
        embed.set_footer(text="Razy HUB • Scripts Premium")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="avatar", description="🖼️ Voir l'avatar d'un membre")
    @app_commands.describe(membre="Membre (toi par défaut)")
    async def avatar(self, interaction: discord.Interaction, membre: discord.Member = None):
        m = membre or interaction.user
        embed = discord.Embed(title=f"🖼️ Avatar de {m.display_name}", color=BLUE)
        embed.set_image(url=m.display_avatar.url)
        embed.add_field(name="🔗 Lien", value=f"[Télécharger]({m.display_avatar.url})", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="annonce", description="📢 Envoyer une annonce pro")
    @app_commands.describe(titre="Titre", message="Contenu", mention="none/everyone/here", couleur="rouge/or/vert/bleu/orange", salon="Salon cible (actuel par défaut)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def annonce(self, interaction: discord.Interaction, titre: str, message: str, mention: str = "none", couleur: str = "rouge", salon: discord.TextChannel = None):
        couleurs = {"rouge": RED, "or": GOLD, "vert": GREEN, "bleu": BLUE, "orange": ORANGE}
        color = couleurs.get(couleur.lower(), RED)
        ch = salon or interaction.channel

        embed = discord.Embed(title=f"📢 {titre}", description=message, color=color)
        embed.set_author(name="Razy HUB — Annonce Officielle", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.set_footer(text=f"Annoncé par {interaction.user.display_name} • Razy HUB", icon_url=interaction.user.display_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()

        ping = {"everyone": "@everyone", "here": "@here"}.get(mention, "")
        await interaction.response.send_message("✅ Annonce envoyée !", ephemeral=True)
        await ch.send(content=ping or None, embed=embed)


async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
