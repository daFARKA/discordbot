import os
import shutil
from dotenv import load_dotenv
import random
from datetime import datetime

import bilplan_tool
import calendar_tool

import discord
from discord import app_commands
from discord.ext import commands


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
        isGitKeep = False 
        folder = 'images'
        for filename in os.listdir(folder):
            if filename == '.gitkeep':
                isGitKeep = True

            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    if not isGitKeep:
                        os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))

            isGitKeep = False

        await interaction.response.send_message("Image folder cleared.")
    else:
        await interaction.response.send_message("You must be the owner to use this command!")

    
@bot.tree.command(name="bilplan", description="Analyzing of bilplan.")
@app_commands.describe(image_file = "Drag the scan of a bilplan here. (.jpg)")
async def bilplan(interaction: discord.Interaction, image_file: discord.Attachment):
    if interaction.user.id == OWNER_ID:
        imageName = datetime.now().strftime('%d.%m.%Y_%H.%M.%S')
        imagePath = 'images/' + imageName + '.jpg'
        await image_file.save(imagePath)
        await interaction.response.defer()
        bilplan = bilplan_tool.analyze_bilplan(imagePath)
        em = discord.Embed(
            title = "B I L P L A N",
            description = imageName + " saved to server. Events have been created in calendar.",
            color = discord.Color.pink())
        
        for entry in bilplan:
            em.add_field(
                name = entry[0],
                value = entry[1],
                inline = False
            )
        
        
        await interaction.followup.send(embed = em)
        
        #await interaction.followup.send(imageName + " saved to server.\n" + 
        #                                        "The bilplan is: " + "".join(map(str, bilplan)))
        #await interaction.response.send_message(file=discord.File(file_to_send))
        # discord.File(r"c:/Users/...")
    else:
        await interaction.response.send_message("You must be the owner to use this command!")   


@bot.tree.command(name="clear_calendar", description="Clear the bilplan calendar.")
async def clear_calendar(interaction: discord.Interaction):
    if interaction.user.id == OWNER_ID:
        await interaction.response.defer()
        calendar_tool.clear_calendar()
        await interaction.followup.send("Cleared the bilplan calendar.")
    else:
        await interaction.response.send_message("You must be the owner to use this command!")   


@bot.tree.command(name="create_calendar_event", description="Creates an event today in the bilplan calendar.")
async def create_calendar_event(interaction: discord.Interaction, name: str, cinema_nr: int, time: str):
    if interaction.user.id == OWNER_ID:
        await interaction.response.defer()

        if len(time) != 4:
            await interaction.followup.send("Time has not been correctly formatted. (time has to have exactly 4 digits)")
            return
        
        try:
            time_int = int(time)
            if time_int > 2400 or time_int < 0:
                await interaction.followup.send("Time has not been correctly formatted. (time has to be between 0000 and 2400)")
                return
        except ValueError:
            await interaction.followup.send("Time has not been correctly formatted. (time has to be an integer)")
            return

        calendar_tool.create_event_today(name, cinema_nr, time)
        await interaction.followup.send("Created the given event in the bilplan calendar.")
    else:
        await interaction.response.send_message("You must be the owner to use this command!")   

@bot.tree.command(name="shutdown", description="Shutsdown server!")
async def shutdown(interaction: discord.Interaction):
    if interaction.user.id == OWNER_ID:
        os.system("shutdown /s /t 1")
    else:
        await interaction.response.send_message("You must be the owner to use this command!")   


@bot.tree.command(name="listcommands", description="Prints a list of all bot commands.")
async def listcommands(interaction: discord.Interaction):
    em = discord.Embed(
        title="COMMANDS",
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