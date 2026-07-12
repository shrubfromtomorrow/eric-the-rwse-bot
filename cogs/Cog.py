from logging import log
import discord
from discord import Bot, Message, ApplicationContext, Member
from discord.ext import commands
from discord.ext.commands import errors
from datetime import datetime, timedelta, timezone

class Cog(commands.Cog):
  def __init__(self, bot: Bot):
    self.bot = bot

  @commands.command()
  @commands.guild_only()
  @commands.has_guild_permissions(administrator=True)
  async def ping(self, ctx: commands.Context):
    latency_ms = self.bot.latency * 1000
    await ctx.reply(f'Boo! My latency is: {latency_ms:.2f}ms')

  # @commands.Cog.listener()
  # async def on_message_delete(self, message: Message):
  #   log_channel = self.bot.get_channel(1523012846756167760) 
  #   if not log_channel:
  #     log_channel = await self.bot.fetch_channel(1523012846756167760) 
  #   await log_channel.send(f'New log: {message.author.mention} said: ```{message.content}```')

  @commands.Cog.listener()
  async def on_member_update(self, before: Member, after: Member):
    guild = await self.bot.get_guild(995807773138890853)
    kick_role = discord.utils.get(guild.roles, name='Bot Kick Role')
    contacted = ''

    # Skip if user has staff role
    for r in after.roles:
      #role IDs in order: immune (shrub testing land), moderator
      if r.id in [1523015950436270285, 995814248003403837]:
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