import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from cogs.Cog import Cog
import traceback
import time
import json
from datetime import datetime, timezone

intents = discord.Intents.default()
intents.message_content = True
intents.presences = True
intents.members = True

load_dotenv()

# IF YOU NEED A PERSISTENT DATABASE
# from pymongo.mongo_client import MongoClient
# from pymongo.server_api import ServerApi
# Create a new client and connect to the server
# mongo = MongoClient(os.environ['CONNECTION_URI'])
# 
# Send a ping to confirm a successful connection
# try:
#   start_time = time.perf_counter()
#   mongo.admin.command('ping')
#   latency_ms = (time.perf_counter() - start_time) * 1000
# 
#   print("Pinged your deployment. You successfully connected to MongoDB!")
# except Exception as e:
#   print(e)
# 
# IF YOU NEED A PERSISTENT DATABASE

bot = commands.Bot(command_prefix='.', intents=intents, debug_guilds=[995807773138890853])
bot.remove_command('help')
bot.add_cog(Cog(bot))
# IF YOU NEED A PERSISTENT DATABASE
# bot.add_cog(Cog(bot, mongo))

@bot.event
async def on_error(event_name, *args, **kwargs):
    err = traceback.format_exc()
    try:
        float(err)
        await print_error(f"float coming from on_error, {err}")
    except ValueError:
        await print_error(err)

@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    await print_error(f"original message: {ctx.message.content}\n error: {error}")

@bot.event
async def on_application_command_error(ctx: commands.Context, error: commands.CommandError):
    await print_error(f"application command error: {error}")

async def print_error(error_string: str):
    logbook_channel = await bot.fetch_channel(1155699597960818698)
    
    if len(error_string) <= 3900:
        embed = discord.Embed(title="Error Log", description=f'```{error_string}```', color=4491263)
        await logbook_channel.send(embed=embed)
        return
    
    parts = []
    current_part = ""
    
    for line in error_string.split('\n'):
        if len(current_part) + len(line) + 1 > 3900:
            parts.append(current_part)
            current_part = line
        else:
            current_part += '\n' + line if current_part else line
    
    if current_part:
        parts.append(current_part)
    
    for i, part in enumerate(parts):
        embed = discord.Embed(title=f"Error Log (Part `{i + 1}`/`{len(parts)}`)", description=f'```{part}```', color=4491263)
        await logbook_channel.send(embed=embed)


@bot.event
async def on_ready():
    print('\n\n************************ READY ************************\n\n')
    
    print(f"Logged in as {bot.user} ({bot.user.id})")
    for guild in bot.guilds:
        print(guild.name, guild.id)
        
    await bot.change_presence(
        status=discord.Status.online, 
        activity=discord.Activity(type=discord.ActivityType.playing, name="Violently fighting in a 1v1 bingo")
    )

    settings_channel = await bot.fetch_channel(1155699597960818698)
    
    embed = discord.Embed(title='Alive!', color=0xF5BDE6, description=f"""
Awake! Our prefix is `{bot.command_prefix}` 
Our latency: `{(bot.latency * 1000):.2f}` ms""")
    
    await settings_channel.send(embed=embed)
    
@bot.command()
async def emoteid(ctx, emoji: discord.Emoji):
    await ctx.send(f"Emote ID: `{emoji.id}`")

# @bot.command()
# async def userexport(ctx, user_id: str):
#     if ctx.author.id != :
#         return
#     GUILD_ID = 995807773138890853
#     guild = bot.get_guild(GUILD_ID)

#     joined_at = datetime(
#         2025,
#         1,
#         26,
#         17,
#         25,
#         tzinfo=timezone.utc
#     )

#     if guild is None:
#         await ctx.send("I couldn't find that server.")
#         return
#     user_id = int(user_id)
#     total = 0

#     filename = f"user_{user_id}_messages.jsonl"

#     with open(filename, "w", encoding="utf-8") as f:

#         for channel in guild.text_channels:

#             permissions = channel.permissions_for(guild.me)

#             if not permissions.view_channel:
#                 continue

#             if not permissions.read_message_history:
#                 continue

#             look_categories = [
#                 995807773138890854,
#                 1512819993190858833,
#                 1351073644855562291,
#                 1514948325948788877
#             ]

#             if channel.category_id not in look_categories:
#                 continue

#             print(f"Scanning #{channel.name}...")

#             try:
#                 async for message in channel.history(
#                     limit=None,
#                     after=joined_at,
#                     oldest_first=True
#                 ):

#                     if message.author.id != user_id:
#                         continue

#                     data = {
#                         "message_id": str(message.id),
#                         "channel": {
#                             "id": str(channel.id),
#                             "name": channel.name
#                         },
#                         "author": {
#                             "id": str(message.author.id),
#                             "name": str(message.author)
#                         },
#                         "timestamp": message.created_at.isoformat(),
#                         "content": message.content,
#                         "jump_url": message.jump_url,

#                         "attachments": [
#                             {
#                                 "id": str(attachment.id),
#                                 "filename": attachment.filename,
#                                 "url": attachment.url,
#                                 "size": attachment.size
#                             }
#                             for attachment in message.attachments
#                         ],

#                         "reply_to": (
#                             str(message.reference.message_id)
#                             if message.reference
#                             and message.reference.message_id
#                             else None
#                         ),

#                         "edited_at": (
#                             message.edited_at.isoformat()
#                             if message.edited_at
#                             else None
#                         )
#                     }

#                     f.write(json.dumps(data, ensure_ascii=False) + "\n")

#                     total += 1

#                     if total % 1000 == 0:
#                         f.flush()
#                         print(f"Found {total} messages")

#             except discord.Forbidden:
#                 print(f"No access to #{channel.name}")

#             except discord.HTTPException as e:
#                 print(f"HTTP error in #{channel.name}: {e}")

#     print(f"Done! Exported {total} messages.")
#     print(f"Saved to: {filename}")
    

bot.run(os.environ['DISCORD_TOKEN'])
