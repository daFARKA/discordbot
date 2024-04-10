import os
import shutil
from dotenv import load_dotenv

import discord
from discord import app_commands
from discord.ext import commands

import random
from datetime import datetime

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

@bot.tree.command(name="color", description="Choose color.")
@app_commands.describe(colors="Colors to choose from.")
@app_commands.choices(colors=[
    app_commands.Choice(name="blue", value=1),
    app_commands.Choice(name="red", value=2),
    app_commands.Choice(name="green", value=3)
])
async def color(interaction: discord.Interaction, colors: app_commands.Choice[int]):
    await interaction.response.send_message(f"{interaction.user.name} picked {colors.name}")

@bot.tree.command(name="rand_int", description="Returns a pseudo random Integer ∈ [lower_bound, upper_bound].")
async def rand_int(interaction: discord.Interaction, lower_bound: int, upper_bound: int):
    randomInt = random.randint(lower_bound, upper_bound)
    await interaction.response.send_message(f"Random number generated: {randomInt}")

@bot.tree.command(name="save_image", description="Saves the image in the attachment on the server.")
@app_commands.describe(image_file = "Drag the image here.")
async def save_image(interaction: discord.Interaction, image_file: discord.Attachment):
    if interaction.user.id == OWNER_ID:
        imageName = datetime.now().strftime('%d.%m.%Y_%H.%M.%S')
        fileName = 'images/' + imageName + '.jpg'
        await image_file.save(fileName)
        await interaction.response.send_message(imageName + " saved to server.")
    else:
        await interaction.response.send_message("You must be the owner to use this command!")

@bot.tree.command(name="clear_image_folder", description="Removes all images from the image folder on the server.")
async def clear_image_folder(interaction: discord.Interaction):
    if interaction.user.id == OWNER_ID:
            folder = 'images'
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))

            await interaction.response.send_message("Image folder cleared.")
    else:
        await interaction.response.send_message("You must be the owner to use this command!")
    

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