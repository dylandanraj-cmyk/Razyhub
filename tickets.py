import discord
from discord.ext import commands
from discord import app_commands
import datetime
import json
import sqlite3
import asyncio
import io

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

# ══════════════════════════════════════════════════
#  VIEWS PERSISTANTES
# ══════════════════════════════════════════════════

class TicketPanelView(discord.ui.View):
    """Panel principal avec boutons de sélection de catégorie."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🛒 Acheter un script", style=discord.ButtonStyle.success, custom_id="ticket_buy")
    async def buy(self, interaction: discord.Interaction, button: discord.ui.Button):
        await open_ticket(interaction, subject="Achat de script")

    @discord.ui.button(label="🔧 Support technique", style=discord.ButtonStyle.primary, custom_id="ticket_support")
    async def support(self, interaction: discord.Interaction, button: discord.ui.Button):
        await open_ticket(interaction, subject="Support technique")

    @discord.ui.button(label="💎 Info VIP / Prix", style=discord.ButtonStyle.secondary, custom_id="ticket_info")
    async def info(self, interaction: discord.Interaction, button: discord.ui.Button):
        await open_ticket(interaction, subject="Informations / Tarifs")

    @discord.ui.button(label="🤝 Partenariat", style=discord.ButtonStyle.danger, custom_id="ticket_partner")
    async def partner(self, interaction: discord.Interaction, button: discord.ui.Button):
        await open_ticket(interaction, subject="Partenariat")


class TicketControlView(discord.ui.View):
    """Contrôles dans le channel de ticket."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Fermer", style=discord.ButtonStyle.danger, custom_id="ticket_close")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_close(interaction)

    @discord.ui.button(label="📋 Claim", style=discord.ButtonStyle.primary, custom_id="ticket_claim")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_claim(interaction)

    @discord.ui.button(label="📝 Transcript", style=discord.ButtonStyle.secondary, custom_id="ticket_transcript")
    async def transcript_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_transcript(interaction)


class TicketCloseConfirmView(discord.ui.View):
    """Confirmation de fermeture."""
    def __init__(self):
        super().__init__(timeout=30)

    @discord.ui.button(label="✅ Confirmer la fermeture", style=discord.ButtonStyle.danger, custom_id="confirm_close")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await finalize_close(interaction)
        self.stop()

    @discord.ui.button(label="❌ Annuler", style=discord.ButtonStyle.secondary, custom_id="cancel_close")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("❌ Fermeture annulée.", ephemeral=True)
        self.stop()


# ══════════════════════════════════════════════════
#  FONCTIONS TICKET
# ══════════════════════════════════════════════════

async def open_ticket(interaction: discord.Interaction, subject: str):
    """Ouvre un ticket pour un utilisateur."""
    db = get_db()
    try:
        # Vérifie si un ticket ouvert existe déjà
        existing = db.execute(
            "SELECT channel_id FROM tickets WHERE guild_id=? AND user_id=? AND status='open'",
            (interaction.guild.id, interaction.user.id)
        ).fetchone()
        if existing:
            ch = interaction.guild.get_channel(existing["channel_id"])
            if ch:
                await interaction.response.send_message(
                    f"❌ Tu as déjà un ticket ouvert : {ch.mention}", ephemeral=True
                )
                return
            else:
                db.execute("UPDATE tickets SET status='closed' WHERE channel_id=?", (existing["channel_id"],))
                db.commit()

        config = db.execute("SELECT * FROM ticket_config WHERE guild_id=?", (interaction.guild.id,)).fetchone()
        category = None
        if config and config["category_id"]:
            category = interaction.guild.get_channel(config["category_id"])

        support_role = None
        if config and config["support_role"]:
            support_role = interaction.guild.get_role(config["support_role"])

        # Compter tickets pour ID
        count = db.execute("SELECT COUNT(*) as c FROM tickets WHERE guild_id=?", (interaction.guild.id,)).fetchone()["c"] + 1
        channel_name = f"ticket-{str(count).zfill(4)}-{interaction.user.name[:10].lower()}"

        # Permissions
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(
                read_messages=True, send_messages=True, attach_files=True, embed_links=True
            ),
            interaction.guild.me: discord.PermissionOverwrite(
                read_messages=True, send_messages=True, manage_channels=True, manage_messages=True
            )
        }
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(
                read_messages=True, send_messages=True, manage_messages=True
            )

        channel = await interaction.guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"Ticket de {interaction.user} | Sujet: {subject}"
        )

        db.execute(
            "INSERT INTO tickets (guild_id, channel_id, user_id, status, subject, created_at) VALUES (?,?,?,?,?,?)",
            (interaction.guild.id, channel.id, interaction.user.id, "open", subject, datetime.datetime.utcnow().isoformat())
        )
        db.commit()

        # Embed d'accueil dans le ticket
        embed = discord.Embed(
            title=f"🎫 Ticket #{str(count).zfill(4)} — {subject}",
            description=(
                f"Bienvenue {interaction.user.mention} !\n\n"
                f"```\n"
                f"📌 Sujet    : {subject}\n"
                f"👤 Membre   : {interaction.user}\n"
                f"📅 Date     : {datetime.datetime.utcnow().strftime('%d/%m/%Y %H:%M')} UTC\n"
                f"```\n\n"
                f"Un membre du staff va vous répondre dès que possible.\n"
                f"Décrivez votre demande en détail ci-dessous.\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=BLUE
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Razy HUB • Support", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.timestamp = datetime.datetime.utcnow()

        mention_text = f"{interaction.user.mention}"
        if support_role:
            mention_text += f" | {support_role.mention}"

        await channel.send(content=mention_text, embed=embed, view=TicketControlView())
        await interaction.response.send_message(
            f"✅ Ton ticket a été créé : {channel.mention}", ephemeral=True
        )

        # Log
        if config and config["log_channel"]:
            log_ch = interaction.guild.get_channel(config["log_channel"])
            if log_ch:
                log_embed = discord.Embed(
                    title="🎫 Nouveau ticket ouvert",
                    description=f"**Membre :** {interaction.user.mention}\n**Sujet :** {subject}\n**Salon :** {channel.mention}\n**ID :** #{str(count).zfill(4)}",
                    color=GREEN, timestamp=datetime.datetime.utcnow()
                )
                await log_ch.send(embed=log_embed)
    finally:
        db.close()


async def handle_close(interaction: discord.Interaction):
    """Demande confirmation de fermeture."""
    db = get_db()
    try:
        ticket = db.execute("SELECT * FROM tickets WHERE channel_id=? AND status='open'", (interaction.channel.id,)).fetchone()
        if not ticket:
            await interaction.response.send_message("❌ Ce salon n'est pas un ticket actif.", ephemeral=True)
            return

        # Vérif permissions
        is_staff = interaction.user.guild_permissions.manage_channels
        is_owner = ticket["user_id"] == interaction.user.id
        if not (is_staff or is_owner):
            await interaction.response.send_message("❌ Tu n'as pas la permission de fermer ce ticket.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🔒 Fermer le ticket ?",
            description="Confirme la fermeture de ce ticket.\nUn transcript sera généré automatiquement.",
            color=ORANGE
        )
        await interaction.response.send_message(embed=embed, view=TicketCloseConfirmView(), ephemeral=False)
    finally:
        db.close()


async def handle_claim(interaction: discord.Interaction):
    """Claim un ticket pour le staff."""
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("❌ Staff uniquement.", ephemeral=True)
        return

    db = get_db()
    try:
        ticket = db.execute("SELECT * FROM tickets WHERE channel_id=? AND status='open'", (interaction.channel.id,)).fetchone()
        if not ticket:
            await interaction.response.send_message("❌ Pas un ticket actif.", ephemeral=True)
            return
        if ticket["claimed_by"]:
            claimer = interaction.guild.get_member(ticket["claimed_by"])
            await interaction.response.send_message(f"❌ Ticket déjà claim par {claimer.mention if claimer else 'un staff'}.", ephemeral=True)
            return

        db.execute("UPDATE tickets SET claimed_by=? WHERE channel_id=?", (interaction.user.id, interaction.channel.id))
        db.commit()

        embed = discord.Embed(
            title="📋 Ticket Claim",
            description=f"{interaction.user.mention} a pris en charge ce ticket.",
            color=GREEN, timestamp=datetime.datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed)
    finally:
        db.close()


async def handle_transcript(interaction: discord.Interaction):
    """Génère un transcript HTML du ticket."""
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("❌ Staff uniquement.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    messages = []
    async for msg in interaction.channel.history(limit=500, oldest_first=True):
        messages.append(msg)

    html = generate_transcript_html(interaction.channel, messages, interaction.guild)
    file = discord.File(
        fp=io.BytesIO(html.encode("utf-8")),
        filename=f"transcript-{interaction.channel.name}.html"
    )

    db = get_db()
    try:
        config = db.execute("SELECT log_channel FROM ticket_config WHERE guild_id=?", (interaction.guild.id,)).fetchone()
        if config and config["log_channel"]:
            log_ch = interaction.guild.get_channel(config["log_channel"])
            if log_ch:
                await log_ch.send(
                    embed=discord.Embed(title="📝 Transcript généré", description=f"Salon : {interaction.channel.name}", color=BLUE),
                    file=discord.File(fp=io.BytesIO(html.encode("utf-8")), filename=f"transcript-{interaction.channel.name}.html")
                )
    finally:
        db.close()

    await interaction.followup.send("✅ Transcript généré !", file=file, ephemeral=True)


async def finalize_close(interaction: discord.Interaction):
    """Ferme définitivement le ticket."""
    db = get_db()
    try:
        ticket = db.execute("SELECT * FROM tickets WHERE channel_id=? AND status='open'", (interaction.channel.id,)).fetchone()
        if not ticket:
            await interaction.response.send_message("❌ Pas un ticket actif.", ephemeral=True)
            return

        # Transcript auto
        messages = []
        async for msg in interaction.channel.history(limit=500, oldest_first=True):
            messages.append(msg)
        html = generate_transcript_html(interaction.channel, messages, interaction.guild)

        db.execute(
            "UPDATE tickets SET status='closed', closed_at=? WHERE channel_id=?",
            (datetime.datetime.utcnow().isoformat(), interaction.channel.id)
        )
        db.commit()

        # Log avec transcript
        config = db.execute("SELECT log_channel FROM ticket_config WHERE guild_id=?", (interaction.guild.id,)).fetchone()
        if config and config["log_channel"]:
            log_ch = interaction.guild.get_channel(config["log_channel"])
            if log_ch:
                user = interaction.guild.get_member(ticket["user_id"])
                log_embed = discord.Embed(
                    title="🔒 Ticket fermé",
                    description=(
                        f"**Membre :** {user.mention if user else ticket['user_id']}\n"
                        f"**Sujet :** {ticket['subject']}\n"
                        f"**Fermé par :** {interaction.user.mention}\n"
                        f"**Messages :** {len(messages)}"
                    ),
                    color=RED, timestamp=datetime.datetime.utcnow()
                )
                await log_ch.send(
                    embed=log_embed,
                    file=discord.File(fp=io.BytesIO(html.encode("utf-8")), filename=f"transcript-{interaction.channel.name}.html")
                )

        # Envoyer le transcript au membre
        user = interaction.guild.get_member(ticket["user_id"])
        if user:
            try:
                await user.send(
                    embed=discord.Embed(
                        title="🔒 Ton ticket a été fermé",
                        description=f"**Serveur :** {interaction.guild.name}\n**Sujet :** {ticket['subject']}\n\nTu trouveras le transcript en pièce jointe.",
                        color=ORANGE
                    ),
                    file=discord.File(fp=io.BytesIO(html.encode("utf-8")), filename=f"transcript-{interaction.channel.name}.html")
                )
            except:
                pass

        await interaction.response.send_message("🔒 Fermeture dans 5 secondes...")
        await asyncio.sleep(5)
        await interaction.channel.delete(reason=f"Ticket fermé par {interaction.user}")
    finally:
        db.close()


def generate_transcript_html(channel, messages, guild) -> str:
    """Génère un transcript HTML stylé."""
    msgs_html = ""
    for msg in messages:
        content = discord.utils.escape_markdown(msg.content) if msg.content else ""
        content = content.replace("\n", "<br>")
        attachments = ""
        for att in msg.attachments:
            if any(att.filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]):
                attachments += f'<img src="{att.url}" style="max-width:300px;border-radius:8px;margin-top:4px;" /><br>'
            else:
                attachments += f'<a href="{att.url}" style="color:#00bfff;">{att.filename}</a><br>'

        embeds_html = ""
        for emb in msg.embeds:
            embeds_html += f'<div style="border-left:4px solid #{hex(emb.color.value)[2:] if emb.color else "5865F2"};padding:8px;margin:4px 0;background:#2f3136;border-radius:4px;">'
            if emb.title:
                embeds_html += f'<strong style="color:#fff;">{emb.title}</strong><br>'
            if emb.description:
                embeds_html += f'<span style="color:#dcddde;">{emb.description[:500]}</span>'
            embeds_html += "</div>"

        is_bot = "🤖 " if msg.author.bot else ""
        msgs_html += f"""
        <div style="display:flex;gap:12px;padding:8px 16px;margin-bottom:4px;" onmouseover="this.style.background='#32353b'" onmouseout="this.style.background='transparent'">
            <img src="{msg.author.display_avatar.url}" style="width:40px;height:40px;border-radius:50%;flex-shrink:0;" />
            <div>
                <span style="color:{'#faa61a' if msg.author.bot else '#fff'};font-weight:600;">{is_bot}{msg.author.display_name}</span>
                <span style="color:#72767d;font-size:0.75em;margin-left:8px;">{msg.created_at.strftime('%d/%m/%Y %H:%M')}</span>
                <div style="color:#dcddde;margin-top:2px;">{content}</div>
                {attachments}
                {embeds_html}
            </div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Transcript — {channel.name}</title>
<style>
* {{box-sizing:border-box;margin:0;padding:0;}}
body {{font-family:'Whitney','Helvetica Neue',Helvetica,Arial,sans-serif;background:#36393f;color:#dcddde;}}
.header {{background:#2f3136;padding:24px 32px;border-bottom:1px solid #202225;}}
.header h1 {{color:#fff;font-size:1.4em;}}
.header p {{color:#72767d;font-size:0.9em;margin-top:4px;}}
.badge {{display:inline-block;background:#5865f2;color:#fff;font-size:0.75em;padding:2px 8px;border-radius:12px;margin-left:8px;}}
.messages {{padding:16px 0;}}
</style>
</head>
<body>
<div class="header">
  <h1>📄 Transcript — #{channel.name} <span class="badge">{guild.name}</span></h1>
  <p>{len(messages)} messages exportés • Généré le {datetime.datetime.utcnow().strftime('%d/%m/%Y à %H:%M')} UTC</p>
</div>
<div class="messages">
{msgs_html}
</div>
</body>
</html>"""


# ══════════════════════════════════════════════════
#  COG
# ══════════════════════════════════════════════════
class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_view(TicketPanelView())
        bot.add_view(TicketControlView())
        bot.add_view(TicketCloseConfirmView())

    # ── Panel ──
    @app_commands.command(name="ticket-panel", description="🎫 Envoyer le panel de tickets dans ce salon")
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎫 Support — Razy HUB",
            description=(
                "**Besoin d'aide ? Ouvre un ticket !**\n\n"
                "```\n"
                "🛒  Acheter un script\n"
                "🔧  Support technique\n"
                "💎  Infos / Tarifs VIP\n"
                "🤝  Partenariat\n"
                "```\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "Clique sur un bouton ci-dessous pour ouvrir un ticket.\n"
                "Notre équipe te répondra rapidement !\n\n"
                "⚠️ **Un seul ticket actif par personne.**"
            ),
            color=BLUE
        )
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.set_footer(text="Razy HUB • Scripts Premium")
        embed.timestamp = datetime.datetime.utcnow()

        await interaction.response.defer(ephemeral=True)
        msg = await interaction.channel.send(embed=embed, view=TicketPanelView())

        db = get_db()
        try:
            db.execute("""
                INSERT INTO ticket_config (guild_id, panel_message_id, panel_channel_id)
                VALUES (?,?,?)
                ON CONFLICT(guild_id) DO UPDATE SET panel_message_id=?, panel_channel_id=?
            """, (interaction.guild.id, msg.id, interaction.channel.id, msg.id, interaction.channel.id))
            db.commit()
        finally:
            db.close()

        await interaction.followup.send("✅ Panel de tickets déployé !", ephemeral=True)

    # ── Config ──
    @app_commands.command(name="ticket-config", description="⚙️ Configurer le système de tickets")
    @app_commands.describe(
        categorie="Catégorie pour les tickets",
        logs="Salon pour les logs",
        support_role="Rôle staff qui voit les tickets"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_config(
        self,
        interaction: discord.Interaction,
        categorie: discord.CategoryChannel = None,
        logs: discord.TextChannel = None,
        support_role: discord.Role = None
    ):
        db = get_db()
        try:
            db.execute("""
                INSERT INTO ticket_config (guild_id, category_id, log_channel, support_role)
                VALUES (?,?,?,?)
                ON CONFLICT(guild_id) DO UPDATE SET
                category_id=COALESCE(?,category_id),
                log_channel=COALESCE(?,log_channel),
                support_role=COALESCE(?,support_role)
            """, (
                interaction.guild.id,
                categorie.id if categorie else None,
                logs.id if logs else None,
                support_role.id if support_role else None,
                categorie.id if categorie else None,
                logs.id if logs else None,
                support_role.id if support_role else None
            ))
            db.commit()
            config = db.execute("SELECT * FROM ticket_config WHERE guild_id=?", (interaction.guild.id,)).fetchone()
        finally:
            db.close()

        embed = discord.Embed(title="⚙️ Config Tickets", color=BLUE, timestamp=datetime.datetime.utcnow())
        cat = interaction.guild.get_channel(config["category_id"]) if config["category_id"] else None
        log_ch = interaction.guild.get_channel(config["log_channel"]) if config["log_channel"] else None
        sr = interaction.guild.get_role(config["support_role"]) if config["support_role"] else None
        embed.add_field(name="📁 Catégorie", value=cat.mention if cat else "Non définie", inline=True)
        embed.add_field(name="📊 Logs", value=log_ch.mention if log_ch else "Non défini", inline=True)
        embed.add_field(name="🛡️ Rôle Staff", value=sr.mention if sr else "Non défini", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── Add user to ticket ──
    @app_commands.command(name="ticket-add", description="➕ Ajouter un membre au ticket")
    @app_commands.describe(membre="Membre à ajouter")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def ticket_add(self, interaction: discord.Interaction, membre: discord.Member):
        db = get_db()
        try:
            ticket = db.execute("SELECT * FROM tickets WHERE channel_id=? AND status='open'", (interaction.channel.id,)).fetchone()
            if not ticket:
                await interaction.response.send_message("❌ Pas un ticket actif.", ephemeral=True)
                return
        finally:
            db.close()
        await interaction.channel.set_permissions(membre, read_messages=True, send_messages=True)
        await interaction.response.send_message(f"✅ {membre.mention} ajouté au ticket.")

    # ── Remove user from ticket ──
    @app_commands.command(name="ticket-remove", description="➖ Retirer un membre du ticket")
    @app_commands.describe(membre="Membre à retirer")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def ticket_remove(self, interaction: discord.Interaction, membre: discord.Member):
        db = get_db()
        try:
            ticket = db.execute("SELECT * FROM tickets WHERE channel_id=? AND status='open'", (interaction.channel.id,)).fetchone()
            if not ticket:
                await interaction.response.send_message("❌ Pas un ticket actif.", ephemeral=True)
                return
        finally:
            db.close()
        await interaction.channel.set_permissions(membre, overwrite=None)
        await interaction.response.send_message(f"✅ {membre.mention} retiré du ticket.")

    # ── Liste tickets ──
    @app_commands.command(name="ticket-list", description="📋 Liste des tickets ouverts")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def ticket_list(self, interaction: discord.Interaction):
        db = get_db()
        try:
            tickets = db.execute(
                "SELECT * FROM tickets WHERE guild_id=? AND status='open' ORDER BY ticket_id DESC LIMIT 20",
                (interaction.guild.id,)
            ).fetchall()
        finally:
            db.close()

        if not tickets:
            await interaction.response.send_message("✅ Aucun ticket ouvert.", ephemeral=True)
            return

        embed = discord.Embed(title=f"📋 Tickets ouverts ({len(tickets)})", color=BLUE, timestamp=datetime.datetime.utcnow())
        for t in tickets:
            ch = interaction.guild.get_channel(t["channel_id"])
            user = interaction.guild.get_member(t["user_id"])
            claimed = interaction.guild.get_member(t["claimed_by"]) if t["claimed_by"] else None
            embed.add_field(
                name=f"#{t['ticket_id']:04d} — {t['subject']}",
                value=f"👤 {user.mention if user else 'Inconnu'} | 📁 {ch.mention if ch else 'Supprimé'} | {'📋 ' + claimed.mention if claimed else '⏳ Non claim'}",
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(TicketCog(bot))
