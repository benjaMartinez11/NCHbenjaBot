import discord
import os
import random

TOKEN = 'siuu'  # ⚠️ No pongas tu token real en el código público

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

########################################################################################################################################################
# Variables de juego

partida_en_curso = False
jugadores_esperados = 0
jugadores = []
canal_partida = None
roles_jugadores = {}
fase_actual = None  # Puede ser "noche" o "día"
victima_noche = None
mafiosos = []

########################################################################################################################################################

@client.event
async def on_ready():
    print(f'✅ Bot conectado como {client.user}')

@client.event
async def on_message(message):
    global partida_en_curso, jugadores_esperados, jugadores, canal_partida
    global roles_jugadores, fase_actual, victima_noche, mafiosos

    if message.author == client.user:
        return

    contenido = message.content.lower()

########################################################################################################################################################
    # Crear partida

    if contenido.startswith('!mafia crear'):
        if partida_en_curso:
            await message.channel.send("❗ Ya hay una partida en curso.")
            return

        partes = contenido.split()
        if len(partes) != 3 or not partes[2].isdigit():
            await message.channel.send("❌ Uso correcto: `!mafia crear <número de jugadores>`")
            return

        jugadores_esperados = int(partes[2])
        if jugadores_esperados < 1:
            await message.channel.send("⚠️ Debe haber al menos 1 jugador.")
            return

        partida_en_curso = True
        jugadores = []
        canal_partida = message.channel
        roles_jugadores = {}
        fase_actual = None
        mafiosos = []

        await canal_partida.send(
            f"🎲 Partida de Mafia creada para {jugadores_esperados} jugadores.\n"
            f"Usa `!mafia unirme` para participar."
        )

########################################################################################################################################################
    # Unirse a la partida

    elif contenido == '!mafia unirme':
        if not partida_en_curso:
            await message.channel.send("❗ No hay ninguna partida activa.")
            return

        if message.author in jugadores:
            await message.channel.send("⚠️ Ya estás en la partida.")
            return

        jugadores.append(message.author)
        await canal_partida.send(
            f"✅ {message.author.display_name} se ha unido. Jugadores actuales: {len(jugadores)}/{jugadores_esperados}"
        )

        if len(jugadores) == jugadores_esperados:
            await canal_partida.send("🎉 Todos los jugadores se han unido. Asignando roles...")
            await asignar_roles()

########################################################################################################################################################
    # Comando de mafioso para matar (solo permitido en fase de noche)
   
    elif contenido.startswith('!matar'):
        if fase_actual != "noche":
            return  # Ignorar si no es de noche

        if isinstance(message.channel, discord.DMChannel):  # Solo desde mensaje privado
            autor = message.author
            if roles_jugadores.get(autor.id) != "Mafioso":
                await autor.send("❌ No tienes permitido usar este comando.")
                return

            partes = contenido.split()
            if len(partes) != 2:
                await autor.send("⚠️ Uso correcto: `!matar <nombre>`")
                return

            objetivo_nombre = partes[1].lower()
            objetivo = discord.utils.find(lambda u: u.display_name.lower() == objetivo_nombre, jugadores)

            if objetivo:
                victima_noche = objetivo
                await autor.send(f"☠️ Has elegido a **{objetivo.display_name}**. Se procesará al amanecer.")
                await canal_partida.send("🌙 Los mafiosos han elegido a su víctima. Se procesará al amanecer.")
            else:
                await autor.send("❌ No se encontró ese jugador.")

########################################################################################################################################################
    # Comando para iniciar fase de noche (solo para pruebas/manual)
   
    elif contenido == '!mafia noche':
        if not partida_en_curso:
            await message.channel.send("❗ No hay partida en curso.")
            return
        fase_actual = "noche"
        victima_noche = None
        await message.channel.send("🌙 Ha caído la noche. Los mafiosos deben elegir a quién matar por mensaje privado con `!matar <jugador>`.")

########################################################################################################################################################
    # Comando para amanecer y anunciar la muerte

    elif contenido == '!mafia amanecer':
        if fase_actual != "noche":
            await message.channel.send("⚠️ No estamos en la noche.")
            return
        fase_actual = "día"
        if victima_noche:
            await canal_partida.send(f"🌅 Ha amanecido. La víctima fue **{victima_noche.display_name}**.")
        else:
            await canal_partida.send("🌅 Ha amanecido. No hubo víctima esta noche.")
        victima_noche = None

########################################################################################################################################################        

async def asignar_roles():
    global partida_en_curso, jugadores, roles_jugadores, mafiosos

    num_jugadores = len(jugadores)
    roles = generar_roles(num_jugadores)
    random.shuffle(jugadores)
    random.shuffle(roles)

    for jugador, rol in zip(jugadores, roles):
        roles_jugadores[jugador.id] = rol
        if rol == "Mafioso":
            mafiosos.append(jugador)

        try:
            mensaje = f"📩 Tu rol es **{rol}**."
            if rol == "Mafioso":
                mensaje += "\nDurante la noche, usa `!matar <nombre>` por mensaje privado para eliminar a alguien."
            elif rol == "Doctor":
                mensaje += "\nDurante la noche, usa `!curar <nombre>` para proteger a alguien."
            elif rol == "Detective":
                mensaje += "\nDurante la noche, usa `!investigar <nombre>` para conocer su rol."

            await jugador.send(mensaje)
        except:
            print(f"⚠️ No se pudo enviar mensaje privado a {jugador.name}.")

    await canal_partida.send("📬 Roles asignados por mensaje privado. Usa `!mafia noche` para comenzar la noche.")
    # No cerramos la partida todavía
    # jugadores.clear() # Lo comentamos si querés seguir usando la lista

def generar_roles(num_jugadores):
    roles_base = ["Mafioso", "Doctor", "Detective"]
    if num_jugadores <= 3:
        return roles_base[:num_jugadores]
    else:
        return roles_base + ["Ciudadano"] * (num_jugadores - len(roles_base))

client.run(TOKEN)
