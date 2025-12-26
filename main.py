import discord
from discord.ext import commands
from discord import app_commands
import logging
from dotenv import load_dotenv
import os
import yt_dlp
import asyncio
from collections import deque

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
guild_id = os.getenv('GUILD_ID')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

queue = deque()
channel_to_embed = None

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


class View(discord.ui.View): # for buttons

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.green)
    async def skip(self, button, interaction):
        if self.vc.is_playing():
            self.vc.stop()
            await button.response.send_message("Song skipped")
        else:
            await button.response.send_message("No song playing to be skipped")

    @discord.ui.button(label="Pause!", style=discord.ButtonStyle.blurple) #change me
    async def pause(self, button, interaction):
        await button.response.send_message("You have clicked the 2nd button")

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.red)
    async def stop(self, button, interaction):
        self.vc.stop()
        await self.vc.disconnect()
        await button.response.send_message("Music bot stopped")

        

@client.tree.command(name="button", descrition="Displaying a Button", guild=guild_id)
async def myButton(interaction: discord.Interaction):
    await interaction.response.send_message(view = View()) # displays the button from View class




@client.tree.command(name="embed", descrition="Embedding when playing", guild=guild_id) # embedeing for songs playing
async def printer(interaction: discord.Interaction):
    embed = discord.Embed(title="TITLE HERE", url ="URL HERE") # change me
    await interaction.response.send_message(embed=embed)




def get_song_from_queue(query: str):
    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(query, download=False)
        if "entries" in info:
            info = info["entries"][0]
        return {
            "title": info["title"],
            "url": info["url"]
        }


async def play_next(vc: discord.VoiceClient, text_channel: discord.TextChannel):
    if not queue:
        return

    song = queue.popleft()

    source = discord.FFmpegOpusAudio(
        song["url"],
        executable=FFMPEG_PATH,
        **FFMPEG_OPTIONS
    )

    def after(error):
        if error:
            print(error)
        asyncio.run_coroutine_threadsafe(
            play_next(vc, text_channel),
            bot.loop
        )

    vc.play(source, after=after)

    embed = discord.Embed(
        title="Now Playing 🎶",
        description=f"[{song['title']}]({song['url']})"
    )

    view = View(vc)
    await text_channel.send(embed=embed, view=view)
    

@bot.tree.command(name="music", description="Play a song or add it to the queue.")
async def play(interaction: discord.Interaction, song_query: str):
    await interaction.response.defer()

    if not interaction.user.voice:
        await interaction.followup.send("You must be in a voice channel.")
        return

    channel = interaction.user.voice.channel
    vc = interaction.guild.voice_client

    if vc is None:
        vc = await channel.connect()
    elif vc.channel != channel:
        await vc.move_to(channel)

    song = get_song_from_queue(song_query)
    queue.append(song)

    if not vc.is_playing():
        await play_next(vc, interaction.channel)
    else:
        await interaction.followup.send("Added to queue.")







# @bot.event
# async def on_command_error(ctx, error):
#     print(f"Command error: {error}")
#     await ctx.send(f"Error: {error}")



# @bot.tree.command(name="play", description="Play a song or add it to the queue.")
# @app_commands.describe(song_query="Search query")
# async def play(interaction: discord.Interaction, song_query: str):
#     await interaction.response.defer()

#     channel = interaction.user.voice.channel
#     vc = interaction.guild.voice_client

#     if channel is None:
#         await interaction.followup.send("No one in voice channel")
#         return


#     if vc is None:
#         vc = await channel.connect()
#     elif vc.channel != vc.channel:
#         await vc.move_to(channel)

#     query = f"ytsearch:{search}" if "http" not in search else search

#     try:
#         loop = asyncio.get_event_loop()
#         with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
#             info = await loop.run_in_executor(
#                 None,
#                 lambda: ydl.extract_info(query, download=False)
#             )

#         if 'entries' in info:
#             info = info['entries'][0]

#         audio_url = info['url']
#         title = info.get('title', 'Unknown Title')

#     except Exception as e:
#         await ctx.send(f"Error finding audio: {e}")
#         return

#     if vc.is_playing():
#         await ctx.send("Already playing audio. Use `!skip` to skip.")
#         return

#     try:
#         source = discord.FFmpegPCMAudio(
#             audio_url,
#             executable=FFMPEG_PATH,
#             **FFMPEG_OPTIONS
#         )
#         vc.play(source)
#         await ctx.send(f"🎶 Now playing: **{title}**")

#     except Exception as e:
#         await ctx.send(f"Error playing audio: {e}")






bot.run(token)
