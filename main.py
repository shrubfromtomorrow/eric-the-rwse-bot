import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from cogs.Cog import Cog
import traceback
import time

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

bot = commands.Bot(command_prefix='!', intents=intents)
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
  logbook_channel = await bot.fetch_channel(1523012846756167760)
  
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

  settings_channel = await bot.fetch_channel(1523013584349561037)
  
  embed = discord.Embed(title='Alive!', color=4776171, description=f"""
Awake! My prefix is `{bot.command_prefix}` 
My latency: `{round(bot.latency * 1000)}` ms""")

  await settings_channel.send(embed=embed)
  

bot.run(os.environ['DISCORD_TOKEN'])
