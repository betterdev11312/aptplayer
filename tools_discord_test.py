"""Testa o Rich Presence sem precisar tocar musica no app.

Uso: abra o Discord, depois rode:
    python tools_discord_test.py
"""
import sys
import time

from core import discord

print("Application ID:", discord.APP_ID or "(nao configurado)")

if not discord.is_configured():
    print("Falta o APP_ID em core/discord.py - veja DISCORD.md")
    sys.exit(1)

if discord._open_pipe() is None:
    print("O Discord nao esta aberto. Abra e rode de novo.")
    sys.exit(1)

print("Discord encontrado. Conectando...")
if not discord.connect():
    print("Nao consegui conectar. O Application ID esta correto?")
    sys.exit(1)

print("Conectado.")
ok = discord.set_activity(
    {"title": "Psychosocial", "artist": "Slipknot", "video_id": "5abamRO41fE"},
    playing=True, position=41, duration=281,
)
print("Status enviado:", ok)
print()
print(">>> Olhe seu perfil no Discord agora. Deve aparecer:")
print("    Ouvindo AptPlayer")
print("    Psychosocial")
print("    por Slipknot")
print()
print("Mantendo por 30 segundos...")
time.sleep(30)

discord.set_activity(None)
discord.disconnect()
print("Limpo. Teste concluido.")
