import discord
from discord.ext import commands
import logging

bot = commands.Bot(command_prefix='!', intents=intents)

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