import os
from dotenv import load_dotenv

import discord
from discord import app_commands
from discord.ext import commands

import random

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
MAIN_GUILD_ID = os.getenv('MAIN_GUILD_ID')
MAIN_GUILD_ID = int(MAIN_GUILD_ID)
OWNER_ID = os.getenv('OWNER_ID')
OWNER_ID = int(OWNER_ID)

bot = commands.Bot(command_prefix="/", intents=discord.Intents.all())

@bot.event   
async def on_ready():
    print(f"{bot.user} has connected to Discord.")

    print("All of the servers the bot is connected to:")
    for server in bot.guilds:
        print(f"{server.name}(id: {server.id})")
        await bot.tree.sync(guild=discord.Object(id=server.id))

@bot.tree.command(name="sync", description="Syncs all commands globally. (BOT-Owner only!)")
@app_commands.guilds(MAIN_GUILD_ID)
async def sync(interaction: discord.Interaction):
    if interaction.user.id == OWNER_ID:
            await bot.tree.sync()
            await interaction.response.send_message("Command tree synced globally.")
    else:
        await interaction.response.send_message("You must be the owner to use this command!")

@bot.tree.command(name="test", description="My first Command")
async def test(interaction: discord.Interaction):
    await interaction.response.send_message("test!")

@bot.tree.command(name="rand_int", description="Returns a pseudo random Integer ∈ [lower_bound, upper_bound].")
async def rand_int(interaction: discord.Interaction, lower_bound: int, upper_bound: int):
    randomInt = random.randint(lower_bound, upper_bound)
    await interaction.response.send_message(f"Random number generated: {randomInt}")

@bot.tree.command(name="listcommands", description="Prints a list of all bot commands.")
async def listcommands(interaction: discord.Interaction):
    em = discord.Embed(
        title="Help",
        description="List of all global commands:",
        color=discord.Color.blurple())
    em.set_thumbnail(
        url=bot.user.avatar.url)
    
    for slash_command in bot.tree.walk_commands():
        em.add_field(name=slash_command.name, 
                     value=slash_command.description if slash_command.description else "", 
                     inline=False)

    await interaction.response.send_message(embed=em)






bot.run(TOKEN)