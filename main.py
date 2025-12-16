import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

FFMPEG_PATH = os.path.join(os.getcwd(), "bin", "ffmpeg", "ffmpeg.exe")

@bot.event
async def on_ready():
    print(f"We are ready to go in, {bot.user.name}!")
    print("Registered commands:")
    for command in bot.commands:
        print(f"- {command}")


@bot.event
async def on_command_error(ctx, error):
    print(f"Command error: {error}")
    await ctx.send(f"Error: {error}")


@bot.command()
async def play(ctx, *, search: str):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("You're not in a voice channel!")
        return

    channel = ctx.author.voice.channel
    vc = ctx.voice_client

    if vc is None:
        vc = await channel.connect()
    elif vc.channel != channel:
        await vc.move_to(channel)