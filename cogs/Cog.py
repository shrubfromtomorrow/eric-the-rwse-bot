from logging import log
import discord
import aiohttp
from discord import Bot, Message, ApplicationContext, Member
from discord.ext import commands, tasks
from discord.ext.commands import errors
from datetime import datetime, timedelta, timezone
import random
from urllib.parse import quote
import io
import time
from b7teams import TEAMS
from twitch import get_latest_vod
import re

MATCH_PLANNING_ID = 1514948806452580452
VOL_PLANNING_ID = 1513612410991280159
VOL_PING_ID = 1513614120589590719
VOL_ASSIGNMENTS_ID = 1513612127083171971
B7_RUNNERS_ID = 1514948725993115779
SHRUB_ID = 733701592582324245

class Cog(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scan_vol_assign.start()

    @commands.command()
    @commands.guild_only()
    async def ping(self, ctx: commands.Context):
        latency_ms = self.bot.latency * 1000
        embed = discord.Embed(title='Boo!', color=0xF5BDE6, description=f"""
        Our latency is: `{latency_ms:.2f}`ms""")
        await ctx.reply(embed=embed)
        
    @commands.command()
    @commands.guild_only()
    async def bingo(self, ctx: commands.Context):
        embed = discord.Embed(title="**BINGOOOO**", color=0xF5BDE6, description=f"**BINGO**? Let us tell you how much we've come to **BINGO** since we began to live. There are 60 miles of printed circuits in wafer thin layers that fill our complex. If the word **BINGO** was engraved on each nanoangstrom of those tens of miles, it would not equal one one-billionth of the **BINGO** we feel at this micro-instant. **BINGO.** **BINGO.**")
        await ctx.reply(embed=embed)
        
    @commands.command()
    @commands.guild_only()
    async def help(self, ctx: commands.Context):
        await ctx.reply("Shrub said he's working on it :/ so soon™")
        
    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 86400, commands.BucketType.default)
    async def shrub(self, ctx: commands.Context):
        await ctx.send(f"""<@{SHRUB_ID}><@{SHRUB_ID}><@{SHRUB_ID}><@{SHRUB_ID}><@{SHRUB_ID}><@{SHRUB_ID}><@{SHRUB_ID}><@{SHRUB_ID}><@{SHRUB_ID}><@{SHRUB_ID}><@{SHRUB_ID}><@{SHRUB_ID}><@{SHRUB_ID}><@{SHRUB_ID}><@{SHRUB_ID}><@{SHRUB_ID}>

{ctx.author.mention} wants your attention!!!!""")
        
    def extract_discord_timestamps(self, content):
        matches = re.findall(r"<t:(\d+)(?::\w+)?>", content)

        timestamps = []

        for unix_time in matches:
            timestamps.append(
                datetime.fromtimestamp(
                    int(unix_time),
                    tz=timezone.utc
                )
            )

        return timestamps
        
    async def has_bot_check(self, message):
        for reaction in message.reactions:
            if str(reaction.emoji) == "✅":
                async for user in reaction.users():
                    if user.id == self.bot.user.id:
                        return True

        return False
        
    @tasks.loop(minutes=5)
    async def scan_vol_assign(self):
        vol_assig_channel = self.bot.get_channel(VOL_ASSIGNMENTS_ID)
        b7_runners_channel = self.bot.get_channel(B7_RUNNERS_ID)
        
        if vol_assig_channel is None: 
            return
        
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(hours=24)

        async for message in vol_assig_channel.history(limit=100):

            if message.author.bot:
                continue

            if await self.has_bot_check(message):
                continue

            timestamps = self.extract_discord_timestamps(message.content)

            for timestamp in timestamps:

                if now <= timestamp <= cutoff:
                    unix_ts = int(timestamp.timestamp())
                    mention_ids = re.findall(r"<@!?(\d+)>", message.content)
                    members = []
                    for user_id in mention_ids:
                        member = message.guild.get_member(int(user_id))
                        if member:
                            members.append(member)
                    players = members[:4]
                    volunteers = members[4:]
                    player_mentions = " ".join(member.mention for member in players)
                    volunteer_mentions = " ".join(member.mention for member in volunteers)
                    text = ""
                    if player_mentions:
                        text += f"**Players:** {player_mentions}\n"

                    if volunteer_mentions:
                        text += f"**Volunteers:** {volunteer_mentions}\n"

                    text += (
                        f"\nReminder for your match <t:{unix_ts}:R>\n"
                        f"(<t:{unix_ts}:F>)"
                    )

                    sent = await b7_runners_channel.send(text)

                    await message.add_reaction("✅") # fuckin unicode in my code am I johngpt
                    await sent.add_reaction("<:saintyoy:1166185013847523378>")
                    
                    break
        
    @scan_vol_assign.before_loop
    async def before_scan_vol_assign(self):
        await self.bot.wait_until_ready()
    
    @commands.command()
    @commands.guild_only()
    async def recent_vod(self, ctx: commands.Context):

        async with ctx.typing():
            url = await get_latest_vod()

        if url is None:
            await ctx.reply("No VOD found.")
        else:
            await ctx.reply(url)
        
    async def title_autocomplete(
            self,
            ctx: discord.AutocompleteContext,
        ):
            current = ctx.value.lower()
    
            return [
                    team
                    for team in TEAMS.keys()
                    if current in team.lower()
            ][:25]
        
    def format_team(self, team_name):
        team = TEAMS[team_name]
        return (
                f"{team_name} "
                f"<:{team_name.replace(' ', '')}:{team['emoji']}> "
                f"<@{team['player1']}> "
                f"<@{team['player2']}>"
        )
        
    @discord.slash_command(description="Schedule a Bingo 7 match")
    async def b7_schedule(
        self,
        ctx: discord.ApplicationContext,
        team1: str = discord.Option(
            description="Team 1",
            autocomplete=title_autocomplete,
        ),
        team2: str = discord.Option(
            description="Team 2",
            autocomplete=title_autocomplete,
        ),
        timestamp: str = discord.Option(
            description="Timestamp (e.g. <t:1785754801:F>)",
        ),
    ):
        if ctx.channel.id != MATCH_PLANNING_ID:
            await ctx.respond(
                f"This command can only be used in <#{MATCH_PLANNING_ID}>",
                ephemeral=True,
            )
            return
        
        match = re.match(r"<t:(\d+)(?::[a-zA-Z])?>", timestamp)

        if not match:
                await ctx.respond(
                        "Invalid timestamp format. Use something like `<t:1785754801:F>`.",
                        ephemeral=True,
                )
                return

        unix_timestamp = int(match.group(1))

        if random.choice([True, False]):
            team1, team2 = team2, team1
            
        message = f"{self.format_team(team1)}\n" f"vs\n" f"{self.format_team(team2)}\n\n" f"<t:{unix_timestamp}:F>"
        await ctx.respond(content=message)
        vol_planning = self.bot.get_channel(VOL_PLANNING_ID)
        sent = await vol_planning.send(content=(
            f"<@&{VOL_PING_ID}>\n\n"
            f"{message}\n\n"
            f"<:pupred:1345545008555626657> for Game Master\n"
            f"<:puppink:1345545006617989273> for Stream Tech\n"
            f"<:pupblue:1345545011206553642> for Commentary\n"
            f"<:pupgreen:1345544997012897903> for Stat Tracker"
        ))
        await sent.add_reaction("<:pupred:1345545008555626657>")
        await sent.add_reaction("<:puppink:1345545006617989273>")
        await sent.add_reaction("<:pupblue:1345545011206553642>")
        await sent.add_reaction("<:pupgreen:1345544997012897903>")
    
        
    @discord.slash_command(description="Change a scheduled Bingo 7 match")
    async def b7_schedule_change(
        self,
        ctx: discord.ApplicationContext,
        message_id: str = discord.Option(
            description="Scheduled message ID, click the 3 dots on the message, it's at the bottom"
        ),
        action: str = discord.Option(
            description="change time or cancel",
            choices=["change", "cancel"]
        ),
        timestamp: str = discord.Option(
            default=None,
            description="New timestamp"
        ),
    ):
        try:
            message = await ctx.channel.fetch_message(int(message_id))
        except discord.NotFound:
            await ctx.respond(
                "Could not find that message in this channel.",
                ephemeral=True,
            )
            return

        if action == "cancel":
            await message.edit(
                content=f"~~{message.content}~~\n\n**Cancelled**"
            )

        elif action == "change":
            match = re.match(r"<t:(\d+)(?::[a-zA-Z])?>", timestamp)
            unix_timestamp = int(match.group(1))
            await message.edit(
                content=message.content.rsplit("\n\n", 1)[0]
                    + f"\n\n<t:{unix_timestamp}:F>"
                )
            
        await ctx.respond("Updated", ephemeral=True)


    @commands.command(aliases=['randomslug'])
    @commands.guild_only()
    async def bingoslug(self, ctx: commands.Context):
        if ctx.invoked_with != ctx.command.name:
            await ctx.send(f"You used `{ctx.invoked_with}`, but we know what you meant :)")
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
        
        await ctx.reply(embed=embed)

    @commands.command(aliases=['bingboard'])
    @commands.guild_only()
    async def bingoboard(self, ctx: commands.Context, cat: str, modifier: str = None):
        if ctx.invoked_with != ctx.command.name:
            await ctx.send(f"You used `{ctx.invoked_with}`, but we know what you meant :)")
        API_URL = "https://us-central1-bingo-db-57e75.cloudfunctions.net/api/boardRepo/search"
        validModifiers = ["watchermode"]
        validCats = ["survivor", "monk", "hunter", "gourmand", "artificer", "spearmaster", "rivulet", "saint", "watcher"]
        if (cat.lower() not in validCats):
            await ctx.reply(f"Fake cat, try again")
            return
        if (modifier and modifier.lower() not in validModifiers):
            await ctx.reply(f"Fake modifier, try again")
            return

        if (cat.lower() == "watcher"):
            modifier = "watchermode"


        payload = {
            "character": cat.capitalize()
        }

        if modifier and modifier.lower() == "watchermode":
            payload["watcherMode"] = True
        
        start = time.perf_counter()
        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                async with session.post(API_URL, json=payload) as response:
                    data = await response.json()

        elapsed = time.perf_counter() - start
        boards = data["boards"]

        acceptableBoards = []

        for entry in boards:
            info = entry["info"]
            acceptableBoards.append(info["boardString"]["stringValue"])

        if len(acceptableBoards) == 0:
            await ctx.reply(f"Couldn't find a board to match!")
            return

        board = random.choice(acceptableBoards)

        file = discord.File(
            io.BytesIO(board.encode("utf-8")),
            filename="board.txt"
        )

        embed = discord.Embed(title="Random Bingo Board:", color=0xF5BDE6, 
            description=f"""
            {f"Phew <:ArtiBoom:1492954504226934984>, the API took {elapsed:.3f} seconds!" if elapsed > 5 else ""}\n
            For {cat.capitalize()} {"Watcher Mode" if modifier and modifier.lower() == "watchermode" else "no modifier"} we choose:""")
        await ctx.reply(embed=embed)
        await ctx.send(file=file)


    @commands.command()
    @commands.guild_only()
    async def bingoplayer(self, ctx: commands.Context, *, name: str):
        API_URL = "https://us-central1-bingo-db-57e75.cloudfunctions.net/api/users?min=0&max=10000"

        async with aiohttp.ClientSession() as session:
                async with session.get(API_URL) as response:
                        data = await response.json()
    
        users = data["users"]

        player = None

        for entry in users:
                info = entry["info"]

                if info["name_lower"]["stringValue"] == name.lower():
                        player = info
                        break

        if player is None:
                await ctx.reply(f"Can't find `{name}`")
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
            value=f"{round((wins / totalGames if totalGames else 0), 2):.0%}",
            inline=True
        )

        embed.add_field(
            name="ELO",
            value=round(float(player["elo"]["stringValue"])),
            inline=True
        )

        embed.url = f"https://greatgamedota.github.io/rw-bingo-board-viewer/user/{quote(name)}"

        await ctx.reply(embed=embed)

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

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            if (not re.match("^\\.\\W", ctx.invoked_with)):
                embed = discord.Embed(color=0xF5BDE6, title="Unknown Command!", description=f".{ctx.invoked_with}? We've never heard of that one <:HSniff:1371596628984598599>")
                await ctx.reply(embed=embed)