from logging import log
import discord
import aiohttp
from discord import Bot, Message, ApplicationContext, Member
from discord.ext import commands
from discord.ext.commands import errors
from datetime import datetime, timedelta, timezone
import random
from urllib.parse import quote

class Cog(commands.Cog):
  def __init__(self, bot: Bot):
    self.bot = bot

  @commands.command()
  @commands.guild_only()
  async def ping(self, ctx: commands.Context):
    latency_ms = self.bot.latency * 1000
    embed = discord.Embed(title='Boo!', color=0xF5BDE6, description=f"""
    Our latency is: {latency_ms:.2f}ms""")
    await ctx.channel.send(embed=embed)


  @commands.command()
  @commands.guild_only()
  async def bingoslug(self, ctx: commands.Context):
    slugs = {"Monk": "https://static.wikitide.net/rainworldwiki/3/37/Monk_select_screen_layer.png", 
             "Survivor": "https://static.wikitide.net/rainworldwiki/6/64/Survivor_select_screen_layer.png", 
             "Hunter": "https://static.wikitide.net/rainworldwiki/7/7d/Hunter_select_screen_layer.png", 
             "Gourmand": "https://static.wikitide.net/rainworldwiki/d/da/Gourmand_select_screen_layer.png", 
             "Artificer": "https://static.wikitide.net/rainworldwiki/e/e3/Artificer_select_screen_layer.png", 
             "Rivulet": "https://static.wikitide.net/rainworldwiki/5/54/Rivulet_select_screen_layer.png", 
             "Spearmaster": "https://static.wikitide.net/rainworldwiki/6/60/Spearmaster_select_screen_layer.png", 
             "Saint": "https://static.wikitide.net/rainworldwiki/4/41/Saint_select_screen_layer.png", 
             "Watcher": "https://static.wikitide.net/rainworldwiki/7/72/Watcher_select_screen_layer.png"}
    slug = random.choice(list(slugs.keys()))
    embed = discord.Embed(title="Random Bingo Slugcat:", color=0xF5BDE6, description=f"We choose {slug}!")
    embed.set_image(url=slugs[slug])

    if (random.random() < 0.005):
      embed = discord.Embed(title="Random Bingo Slugcat:", color=0xF5BDE6, description=f"We choose INV! <:PeachSilly:1515733112905011260>")
      embed.set_image(url="https://static.wikitide.net/rainworldwiki/3/3c/DatingSim_blush.gif")
    
    await ctx.channel.send(embed=embed)


  @commands.command()
  @commands.guild_only()
  async def bingoplayer(self, ctx: commands.Context, *, name: str):
    API_URL = "https://us-central1-bingo-db-57e75.cloudfunctions.net/api/users"

    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as response:
            data = await response.json()
  
    users = data["users"]

    player = None

    print(name)
    for entry in users:
        info = entry["info"]

        if info["name_lower"]["stringValue"] == name.lower():
            player = info
            break

    if player is None:
        await ctx.send(f"Could not find player `{name}`.")
        return

    embed = discord.Embed(
    title=f"{player['name']['stringValue']}'s Bingo Stats",
    color=0xF5BDE6
    )

    wins = int(player.get("wins", {}).get("integerValue", "0"))
    totalGames = int(player.get("gamesPlayed", {}).get("integerValue", "0"))

    embed.add_field(
        name="Wins",
        value=wins,
        inline=True
    )

    embed.add_field(
        name="Games Played",
        value=totalGames,
        inline=True
    )

    embed.add_field(
      name="Winrate",
      value=f"{round(wins/totalGames, 2):.0%}",
      inline=True
    )

    embed.add_field(
      name="ELO",
      value=round(float(player["elo"]["stringValue"])),
      inline=True
    )

    embed.url = f"https://greatgamedota.github.io/rw-bingo-board-viewer/user/{quote(name)}"

    await ctx.send(embed=embed)

  @commands.Cog.listener()
  async def on_member_update(self, before: Member, after: Member):
    await self.handle_bot_autokick(before, after)
    await self.handle_new_feature(before, after)

  async def handle_bot_autokick(self, before: Member, after: Member):
    guild = await self.bot.fetch_guild(995807773138890853)
    kick_role = discord.utils.get(guild.roles, name='Bot Kick Role')
    contacted = ''

    # Skip if user has staff role
    for r in after.roles:
      #role IDs in order: moderator
      if r.id in [995814248003403837]:
        return

    if kick_role in after.roles:
      try:
        await after.send(content=f"""# Account auto-kicked: Bot detected\nYour account was removed from the server for selecting one of the options on the final onboarding question, called "I AM a Bot!"\n\nThis question is meant to kick out scam accounts or botted accounts that try to self-assign every role upon joining the server.\n**Please skip the last question and do not select the "I AM a Bot!" option!**\n\nYou may rejoin the server by [clicking here](https://discord.gg/RWSE)""")
      except Exception as e:
        if str(e)[0:3] == '403':
          contacted = '. User had DMs disabled, not contacted.'
          pass
        else:
          raise e

      await self.bot.get_channel(1155699597960818698).send(f"# Suspected Bot Autokick\n<@{after.id}> / {after.id}{contacted}")
      await after.remove_roles(kick_role)
      await after.kick(reason=f"Self-selected the bot auto-kick role{contacted}")
  
  async def handle_new_feature(self, before: Member, after: Member):
    guild = await self.bot.fetch_guild(995807773138890853)
    vol_role = discord.utils.get(guild.roles, name='Volunteer')
    pre_vol_role = discord.utils.get(guild.roles, name='Previous Volunteer')

    if vol_role in before.roles and vol_role not in after.roles:
      await self.bot.get_channel(1155699597960818698).send(f"# Volunteer role was removed for \n<@{after.id}>. Added Previous Volunteer")
      await after.add_roles(pre_vol_role)