import discord
from discord.ext import commands
from discord import app_commands
import datetime
import json
import sqlite3

def get_db():
    conn = sqlite3.connect("razy.db")
    conn.row_factory = sqlite3.Row
    return conn

RED    = discord.Color.from_rgb(255, 60, 60)
GREEN  = discord.Color.from_rgb(50, 205, 50)
BLUE   = discord.Color.from_rgb(0, 191, 255)
ORANGE = discord.Color.from_rgb(255, 140, 0)
GRAY   = discord.Color.from_rgb(100, 100, 100)


class AutomodCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ══════════════════════════════════════════════
    #  ANTI-LINK CONFIG
    # ══════════════════════════════════════════════
    @app_commands.command(name="antilink", description="🔗 Configurer l'anti-lien")
    @app_commands.describe(
        activer="Activer ou désactiver",
        action="Action : delete / warn / mute / kick / ban"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def antilink(self, interaction: discord.Interaction, activer: bool, action: str = "delete"):
        valid_actions = ["delete", "warn", "mute", "kick", "ban"]
        if action not in valid_actions:
            await interaction.response.send_message(f"❌ Action invalide. Choix : {', '.join(valid_actions)}", ephemeral=True)
            return

        db = get_db()
        try:
            db.execute("""
                INSERT INTO antilink (guild_id, enabled, action)
                VALUES (?,?,?)
                ON CONFLICT(guild_id) DO UPDATE SET enabled=?, action=?
            """, (interaction.guild.id, int(activer), action, int(activer), action))
            db.commit()
        finally:
            db.close()

        status = "✅ Activé" if activer else "❌ Désactivé"
        embed = discord.Embed(
            title="🔗 Anti-lien configuré",
            description=f"**Statut :** {status}\n**Action :** `{action}`\n\nUtilise `/antilink-whitelist` pour exclure des rôles/salons.",
            color=GREEN if activer else GRAY,
            timestamp=datetime.datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="antilink-whitelist", description="🔗 Gérer la whitelist anti-lien")
    @app_commands.describe(
        type_item="role ou channel",
        action="add ou remove",
        role="Rôle à exclure",
        salon="Salon à exclure"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def antilink_whitelist(
        self,
        interaction: discord.Interaction,
        type_item: str,
        action: str,
        role: discord.Role = None,
        salon: discord.TextChannel = None
    ):
        db = get_db()
        try:
            row = db.execute("SELECT * FROM antilink WHERE guild_id=?", (interaction.guild.id,)).fetchone()
            if not row:
                await interaction.response.send_message("❌ Configure d'abord l'anti-lien avec `/antilink`.", ephemeral=True)
                return

            if type_item == "role" and role:
                wl = json.loads(row["whitelist_roles"])
                if action == "add":
                    if role.id not in wl:
                        wl.append(role.id)
                    msg = f"✅ Rôle {role.mention} ajouté à la whitelist."
                else:
                    wl = [r for r in wl if r != role.id]
                    msg = f"✅ Rôle {role.mention} retiré de la whitelist."
                db.execute("UPDATE antilink SET whitelist_roles=? WHERE guild_id=?", (json.dumps(wl), interaction.guild.id))

            elif type_item == "channel" and salon:
                wl = json.loads(row["whitelist_channels"])
                if action == "add":
                    if salon.id not in wl:
                        wl.append(salon.id)
                    msg = f"✅ Salon {salon.mention} ajouté à la whitelist."
                else:
                    wl = [c for c in wl if c != salon.id]
                    msg = f"✅ Salon {salon.mention} retiré de la whitelist."
                db.execute("UPDATE antilink SET whitelist_channels=? WHERE guild_id=?", (json.dumps(wl), interaction.guild.id))
            else:
                await interaction.response.send_message("❌ Paramètres invalides.", ephemeral=True)
                return

            db.commit()
        finally:
            db.close()

        await interaction.response.send_message(msg, ephemeral=True)

    @app_commands.command(name="antilink-status", description="📊 Voir la config anti-lien")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def antilink_status(self, interaction: discord.Interaction):
        db = get_db()
        try:
            row = db.execute("SELECT * FROM antilink WHERE guild_id=?", (interaction.guild.id,)).fetchone()
        finally:
            db.close()

        if not row:
            await interaction.response.send_message("❌ Anti-lien non configuré.", ephemeral=True)
            return

        wl_roles = json.loads(row["whitelist_roles"])
        wl_channels = json.loads(row["whitelist_channels"])

        roles_txt = " ".join(f"<@&{r}>" for r in wl_roles) or "Aucun"
        chans_txt = " ".join(f"<#{c}>" for c in wl_channels) or "Aucun"

        embed = discord.Embed(title="🔗 Anti-lien — Statut", color=BLUE, timestamp=datetime.datetime.utcnow())
        embed.add_field(name="📊 Statut", value="✅ Activé" if row["enabled"] else "❌ Désactivé", inline=True)
        embed.add_field(name="⚡ Action", value=f"`{row['action']}`", inline=True)
        embed.add_field(name="🎭 Rôles whitelist", value=roles_txt, inline=False)
        embed.add_field(name="💬 Salons whitelist", value=chans_txt, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ══════════════════════════════════════════════
    #  AUTOMOD CONFIG
    # ══════════════════════════════════════════════
    @app_commands.command(name="automod", description="🛡️ Configurer l'automod complet")
    @app_commands.describe(
        anti_spam="Anti-spam activé",
        spam_seuil="Messages avant sanction (défaut: 5)",
        spam_intervalle="Intervalle en secondes (défaut: 5)",
        anti_caps="Anti-majuscules activé",
        caps_seuil="% de majuscules max (défaut: 70)",
        anti_mention="Anti-mention spam activé",
        mention_seuil="Nombre de mentions max (défaut: 5)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def automod(
        self,
        interaction: discord.Interaction,
        anti_spam: bool = None,
        spam_seuil: int = 5,
        spam_intervalle: int = 5,
        anti_caps: bool = None,
        caps_seuil: int = 70,
        anti_mention: bool = None,
        mention_seuil: int = 5
    ):
        db = get_db()
        try:
            current = db.execute("SELECT * FROM automod WHERE guild_id=?", (interaction.guild.id,)).fetchone()

            values = {
                "anti_spam": int(anti_spam) if anti_spam is not None else (current["anti_spam"] if current else 0),
                "spam_threshold": spam_seuil,
                "spam_interval": spam_intervalle,
                "anti_caps": int(anti_caps) if anti_caps is not None else (current["anti_caps"] if current else 0),
                "caps_threshold": caps_seuil,
                "anti_mention": int(anti_mention) if anti_mention is not None else (current["anti_mention"] if current else 0),
                "mention_threshold": mention_seuil
            }

            db.execute("""
                INSERT INTO automod (guild_id, anti_spam, spam_threshold, spam_interval, anti_caps, caps_threshold, anti_mention, mention_threshold)
                VALUES (?,?,?,?,?,?,?,?)
                ON CONFLICT(guild_id) DO UPDATE SET
                anti_spam=?, spam_threshold=?, spam_interval=?,
                anti_caps=?, caps_threshold=?,
                anti_mention=?, mention_threshold=?
            """, (
                interaction.guild.id,
                values["anti_spam"], values["spam_threshold"], values["spam_interval"],
                values["anti_caps"], values["caps_threshold"],
                values["anti_mention"], values["mention_threshold"],
                values["anti_spam"], values["spam_threshold"], values["spam_interval"],
                values["anti_caps"], values["caps_threshold"],
                values["anti_mention"], values["mention_threshold"]
            ))
            db.commit()
        finally:
            db.close()

        def status(v): return "✅" if v else "❌"

        embed = discord.Embed(title="🛡️ Automod configuré", color=GREEN, timestamp=datetime.datetime.utcnow())
        embed.add_field(
            name="🚫 Anti-Spam",
            value=f"{status(values['anti_spam'])} | {values['spam_threshold']} msg / {values['spam_interval']}s → Mute 5min",
            inline=False
        )
        embed.add_field(
            name="🔤 Anti-Caps",
            value=f"{status(values['anti_caps'])} | Seuil : {values['caps_threshold']}% → Suppression",
            inline=False
        )
        embed.add_field(
            name="📣 Anti-Mention",
            value=f"{status(values['anti_mention'])} | Max {values['mention_threshold']} mentions → Mute",
            inline=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ══════════════════════════════════════════════
    #  REACTION ROLES
    # ══════════════════════════════════════════════
    @app_commands.command(name="reactionrole", description="🎨 Créer un message de reaction roles")
    @app_commands.describe(
        titre="Titre", description="Description",
        emoji1="Emoji 1", role1="Rôle 1",
        emoji2="Emoji 2", role2="Rôle 2",
        emoji3="Emoji 3", role3="Rôle 3",
        emoji4="Emoji 4", role4="Rôle 4"
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    async def reactionrole(
        self, interaction: discord.Interaction,
        titre: str, description: str,
        emoji1: str, role1: discord.Role,
        emoji2: str = None, role2: discord.Role = None,
        emoji3: str = None, role3: discord.Role = None,
        emoji4: str = None, role4: discord.Role = None
    ):
        pairs = [(emoji1, role1)]
        for e, r in [(emoji2, role2), (emoji3, role3), (emoji4, role4)]:
            if e and r:
                pairs.append((e, r))

        desc = f"{description}\n\n━━━━━━━━━━━━━━━━━━━━━━\n"
        for emoji, r in pairs:
            desc += f"{emoji} → {r.mention}\n"

        embed = discord.Embed(title=f"🎨 {titre}", description=desc, color=BLUE)
        embed.set_footer(text="Razy HUB • Réagis pour obtenir un rôle !")
        embed.timestamp = datetime.datetime.utcnow()

        await interaction.response.send_message("✅ Créé !", ephemeral=True)
        msg = await interaction.channel.send(embed=embed)

        db = get_db()
        try:
            for emoji, r in pairs:
                db.execute(
                    "INSERT OR REPLACE INTO reaction_roles (message_id, emoji, role_id, guild_id) VALUES (?,?,?,?)",
                    (msg.id, str(emoji), r.id, interaction.guild.id)
                )
                await msg.add_reaction(emoji)
            db.commit()
        finally:
            db.close()

    # ══════════════════════════════════════════════
    #  SETUP / RESET SERVEUR
    # ══════════════════════════════════════════════
    @app_commands.command(name="setup", description="🚀 Générer le serveur Razy HUB")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            await build_server(interaction.guild, interaction.user)
            await interaction.followup.send("✅ **Serveur Razy HUB généré !** Rôle Owner assigné.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erreur : `{e}`", ephemeral=True)

    @app_commands.command(name="reset", description="🔄 Reset complet du serveur")
    @app_commands.checks.has_permissions(administrator=True)
    async def reset(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            await build_server(interaction.guild, interaction.user)
            await interaction.followup.send("🔄 **Reset terminé !**", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erreur : `{e}`", ephemeral=True)


# ══════════════════════════════════════════════════
#  BUILD SERVER (importé depuis main originalement)
# ══════════════════════════════════════════════════
async def build_server(guild, user):
    import asyncio
    RED    = discord.Color.from_rgb(255, 60, 60)
    GOLD   = discord.Color.from_rgb(255, 215, 0)
    GREEN  = discord.Color.from_rgb(50, 205, 50)
    BLUE   = discord.Color.from_rgb(0, 191, 255)
    ORANGE = discord.Color.from_rgb(255, 140, 0)
    GRAY   = discord.Color.from_rgb(100, 100, 100)

    tasks = [ch.delete() for ch in guild.channels]
    await asyncio.gather(*tasks, return_exceptions=True)
    for role in guild.roles:
        if role.name != "@everyone" and not role.managed:
            try:
                await role.delete()
            except:
                pass

    r_owner  = await guild.create_role(name="👑 Owner",  color=GOLD,   hoist=True, permissions=discord.Permissions.all())
    r_admin  = await guild.create_role(name="⚡ Admin",   color=RED,    hoist=True, permissions=discord.Permissions(administrator=True))
    r_staff  = await guild.create_role(name="🛡️ Staff",  color=ORANGE, hoist=True, permissions=discord.Permissions(manage_messages=True, kick_members=True, mute_members=True, read_messages=True, send_messages=True))
    r_vip    = await guild.create_role(name="💎 VIP",     color=BLUE,   hoist=True, permissions=discord.Permissions(read_messages=True, send_messages=True))
    r_member = await guild.create_role(name="👤 Membre",  color=GRAY,   hoist=True, permissions=discord.Permissions(read_messages=True, send_messages=True, add_reactions=True))

    ev = guild.default_role
    pub  = {ev: discord.PermissionOverwrite(read_messages=True, send_messages=False)}
    chat = {ev: discord.PermissionOverwrite(read_messages=False), r_member: discord.PermissionOverwrite(read_messages=True, send_messages=True), r_vip: discord.PermissionOverwrite(read_messages=True, send_messages=True), r_staff: discord.PermissionOverwrite(read_messages=True, send_messages=True), r_admin: discord.PermissionOverwrite(read_messages=True, send_messages=True), r_owner: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
    staf = {ev: discord.PermissionOverwrite(read_messages=False), r_staff: discord.PermissionOverwrite(read_messages=True, send_messages=True), r_admin: discord.PermissionOverwrite(read_messages=True, send_messages=True), r_owner: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
    hide = {ev: discord.PermissionOverwrite(read_messages=False)}
    open_= {ev: discord.PermissionOverwrite(read_messages=True)}

    cat_sup  = await guild.create_category("🎫 Support",   overwrites=hide)
    await guild.create_text_channel("🎫・tickets", category=cat_sup, overwrites=chat)
    await guild.create_text_channel("❓・faq",     category=cat_sup, overwrites=pub)

    cat_main = await guild.create_category("📢 Main",      overwrites=open_)
    ch_news  = await guild.create_text_channel("📢・news",            category=cat_main, overwrites=pub)
    ch_purch = await guild.create_text_channel("🛒・purchase",        category=cat_main, overwrites=pub)
    ch_pay   = await guild.create_text_channel("💳・paiement",        category=cat_main, overwrites=pub)
    ch_rules = await guild.create_text_channel("📜・règlement",       category=cat_main, overwrites=pub)

    cat_hub  = await guild.create_category("🚀 Hub",       overwrites=open_)
    await guild.create_text_channel("⚙️・executors",  category=cat_hub, overwrites=pub)
    await guild.create_text_channel("👥・steals",     category=cat_hub, overwrites=pub)
    ch_razy  = await guild.create_text_channel("🟢・razy-hub",        category=cat_hub, overwrites=pub)

    cat_com  = await guild.create_category("💬 Communauté", overwrites=hide)
    ch_welc  = await guild.create_text_channel("🌴・welcome",         category=cat_com, overwrites=pub)
    await guild.create_text_channel("☁️・chat",       category=cat_com, overwrites=chat)
    await guild.create_text_channel("📸・showcase",   category=cat_com, overwrites=chat)
    await guild.create_text_channel("✅・proofs",     category=cat_com, overwrites=chat)
    await guild.create_voice_channel("📞 VC Général", category=cat_com)

    cat_stf  = await guild.create_category("🛡️ Staff",     overwrites=hide)
    await guild.create_text_channel("📋・général",    category=cat_stf, overwrites=staf)
    ch_logs  = await guild.create_text_channel("📊・logs",       category=cat_stf, overwrites=staf)
    await guild.create_text_channel("🚨・sanctions",  category=cat_stf, overwrites=staf)
    await guild.create_voice_channel("🛡️ Staff VC",   category=cat_stf, overwrites=staf)

    # Envoie les embeds d'accueil
    await ch_news.send(embed=discord.Embed(title="📢 Razy HUB — News", description="Bienvenue sur **Razy HUB** !\nToutes les annonces officielles ici.", color=RED).set_footer(text="Razy HUB • Scripts Premium"))
    await ch_welc.send(embed=discord.Embed(title="🌴 Bienvenue sur Razy HUB !", description="Le serveur officiel de **Razy HUB** — Scripts Roblox premium.\n\n🟢 **Notre script :** `razy-hub`\n🛒 **Acheter →** `#purchase`\n🎫 **Support →** `#tickets`\n\n━━━━━━━━━━━━━━━━━━━━━━\n✅ Bon jeu !", color=RED).set_footer(text="Razy HUB • Scripts Premium"))
    await ch_purch.send(embed=discord.Embed(title="🛒 Nos offres — Razy HUB", description="━━━━━━━━━━━━━━━━━━━━━━\n🔥 **Pack Starter** — X€\n> Accès Razy HUB de base\n\n💎 **Pack Premium** — X€\n> Accès complet + mises à jour\n\n👑 **Pack VIP** — X€\n> Tout inclus + support prioritaire\n\n━━━━━━━━━━━━━━━━━━━━━━\n📩 Ouvre un ticket pour acheter !", color=GOLD).set_footer(text="Razy HUB • Scripts Premium"))
    await ch_razy.send(embed=discord.Embed(title="🟢 Razy HUB", description="Le script officiel **Razy HUB**.\n\n> Toutes les infos, loadstring et mises à jour ici.", color=GREEN).set_footer(text="Razy HUB • Scripts Premium"))
    await ch_rules.send(embed=discord.Embed(title="📜 Règlement — Razy HUB", description="**1.** Respecte tous les membres\n**2.** Pas de spam ou flood\n**3.** Pas de liens non autorisés\n**4.** Pas de pub sans autorisation\n**5.** Obéis au staff\n**6.** Pas de NSFW\n**7.** Un seul compte par personne\n\n*Le non-respect entraîne des sanctions.*", color=RED).set_footer(text="Razy HUB • Règlement Officiel"))

    # Config logs dans la DB
    db = get_db()
    try:
        db.execute("""
            INSERT INTO ticket_config (guild_id, log_channel)
            VALUES (?,?)
            ON CONFLICT(guild_id) DO UPDATE SET log_channel=?
        """, (guild.id, ch_logs.id, ch_logs.id))
        db.commit()
    finally:
        db.close()

    try:
        await user.add_roles(r_owner, r_admin)
    except:
        pass


async def setup(bot):
    await bot.add_cog(AutomodCog(bot))
