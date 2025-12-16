import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import yt_dlp
import asyncio

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

FFMPEG_PATH = os.path.join(os.getcwd(), "bin", "ffmpeg", "ffmpeg.exe")

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'youtube_include_dash_manifest': False,
    'youtube_include_hls_manifest': False,
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -c:a libopus -b:a 96k',
}

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

    query = f"ytsearch:{search}" if "http" not in search else search

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = await loop.run_in_executor(
                None,
                lambda: ydl.extract_info(query, download=False)
            )

        if 'entries' in info:
            info = info['entries'][0]

        audio_url = info['url']
        title = info.get('title', 'Unknown Title')

    except Exception as e:
        await ctx.send(f"Error finding audio: {e}")
        return

    if vc.is_playing():
        await ctx.send("Already playing audio. Use `!skip` to skip.")
        return

    try:
        source = discord.FFmpegPCMAudio(
            audio_url,
            executable=FFMPEG_PATH,
            **FFMPEG_OPTIONS
        )
        vc.play(source)
        await ctx.send(f"🎶 Now playing: **{title}**")

    except Exception as e:
        await ctx.send(f"Error playing audio: {e}")


@bot.command()
async def skip(ctx):
    vc = ctx.voice_client
    if vc and (vc.is_playing() or vc.is_paused()):
        vc.stop()
        await ctx.send("Skipped current song.")
    else:
        await ctx.send("Nothing is playing.")





bot.run(token)
