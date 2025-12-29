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
    'quiet': True,
    'extract_flat': False,  
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # for IPv6 issues
} 

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}


@bot.event
async def on_ready():
    # shows bot is in discord
    guild = discord.Object(id=int(guild_id))
    await bot.tree.sync(guild=guild)

    print(f"We are ready to go in, {bot.user.name}!")
    print("Slash commands synced to guild:", guild_id)


class View(discord.ui.View):
    # for the buttons underneeth the song playing (skip, pause/resume, stop)
    def __init__(self, vc: discord.VoiceClient):
        super().__init__(timeout=None)
        self.vc = vc
        self.paused = False

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.green)
    # stops the song that is playing so that next one can play
    async def skip(self, button, interaction):
        if self.vc.is_playing():
            self.vc.stop()
            await button.response.send_message("Song skipped")
        else:
            await button.response.send_message("No song playing to be skipped")

    @discord.ui.button(label="Pause!", style=discord.ButtonStyle.blurple)
    # will pause and change button label or vis versa
    async def pause_or_resume(self, button, interaction):
        if self.vc.is_playing():
            self.vc.pause()
            button.label = "Resume"
            await interaction.response.edit_message(view=self)
        elif self.vc.is_paused():
            self.vc.resume()
            button.label = "Pause"
            await interaction.response.edit_message(view=self)
        else:
            await interaction.response.send_message("Nothing to pause.", ephemeral=True)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.red)
    # stops song and disconnects
    async def stop(self, button, interaction):
        self.vc.stop()
        await self.vc.disconnect()
        await button.response.send_message("Music bot stopped")

    
def get_song_from_queue(query: str):
    # gets next song and its info from queue
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch',
        'source_address': '0.0.0.0'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if 'entries' in info:  # search returned multiple results
            info = info['entries'][0]

        return {
            'title': info['title'],
            'url': info['url']  # direct audio URL
        }


async def play_next(vc: discord.VoiceClient, text_channel: discord.TextChannel):
    # play the next song in the queue
    if not queue:
        await asyncio.sleep(60) # leave voice channel after 60 seconds if there is not queue
        if not queue and not vc.is_playing():
            await text_channel.send("Leaving voice channel due to inactivity")
            await vc.disconnect()
        return

    song = queue.popleft()

    source = discord.FFmpegOpusAudio(
        song["url"],
        executable=FFMPEG_PATH,
        **FFMPEG_OPTIONS
    )

    def after(error): # after a song finishes it calls play next again
        if error:
            print(error)

        asyncio.run_coroutine_threadsafe(
            play_next(vc, text_channel),
            bot.loop
        )

    vc.play(source, after=after)

    embed = discord.Embed( # embed that appears in discord sdisplaying son info
        title="Now Playing:",
        description=f"[{song['title']}]({song['url']})"
    )

    view = View(vc) # buttons
    await text_channel.send(embed=embed, view=view)
    

@bot.tree.command( name="music", description="Play a song or add it to the queue.", guild=discord.Object(id=int(guild_id)) )
async def play(interaction: discord.Interaction, song_query: str):
    # /music to play song or add it to queue
    await interaction.response.defer()

    if not interaction.user.voice:
        await interaction.followup.send("You must be in a voice channel.")
        return

    channel = interaction.user.voice.channel
    vc = interaction.guild.voice_client

    if vc is None: # put bot into voice channel
        vc = await channel.connect()
    elif vc.channel != channel:
        await vc.move_to(channel)

    song = get_song_from_queue(song_query)
    queue.append(song)

    if not vc.is_playing():
        await play_next(vc, interaction.channel)
    else:
        await interaction.followup.send("Added to queue.")


bot.run(token)