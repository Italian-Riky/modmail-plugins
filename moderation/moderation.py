import datetime
import logging

logger = logging.getLogger("Modmail")

import discord
import typing
from discord.ext import commands

from core import checks
from core.models import PermissionLevel


class ModerationPlugin(commands.Cog):
    """
    Gestisci il tuo server con il miglior plugin al mondo! (plugin tradotto da [Italian Riky](https://github.com/Italian-Riky))
    """

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def moderation(self, ctx: commands.Context):
        """
        Impostazioni e utilità.
        """
        await ctx.send_help(ctx.command)
        return

    @moderation.command()
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """
        Imposta il canale log per le azioni di moderazione.
        """

        await self.db.find_one_and_update(
            {"_id": "config"}, {"$set": {"channel": channel.id}}, upsert=True
        )

        await ctx.send("Fatto!")
        return

    @commands.command(aliases=["banhammer"])
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def ban(
        self,
        ctx: commands.Context,
        members: commands.Greedy[discord.Member],
        days: typing.Optional[int] = 0,
        *,
        reason: str = None,
    ):
        """Banna una o piu persone!
                Uso:
                {prefix}ban @member 10 Pubblicizzano i loro sever.
                {prefix}ban @member1 @member2 @member3 Ascoltano auto blu.
                """

        config = await self.db.find_one({"_id": "config"})

        if config is None:
            return await ctx.send("Non c'è nessun canale dei log configurato.")
        else:
            channel = ctx.guild.get_channel(int(config["channel"]))

        if channel is None:
            await ctx.send("Non c'è nessun canale dei log configurato.")
            return

        try:
            for member in members:
                await member.ban(
                    delete_message_days=days, reason=f"{reason if reason else None}"
                )

                embed = discord.Embed(
                    color=discord.Color.red(),
                    title=f"{member} was banned!",
                    timestamp=datetime.datetime.utcnow(),
                )

                embed.add_field(
                    name="Moderator", value=f"{ctx.author}", inline=False,
                )

                if reason:
                    embed.add_field(name="Reason", value=reason, inline=False)

                await ctx.send(f"🚫 | {member} è stato bannato!")
                await channel.send(embed=embed)

        except discord.Forbidden:
            await ctx.send("Non ho i permessi per bannare le persone.")

        except Exception as e:
            await ctx.send(
                "Errore, Controlla i log per maggiori informazioni."
            )
            logger.error(e)
            return

    @commands.command(aliases=["getout"])
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def kick(
        self, ctx, members: commands.Greedy[discord.Member], *, reason: str = None
    ):
        """Kicka una o piu persone.
        Usage:
        {prefix}kick @member Puzzano
        {prefix}kick @member1 @member2 @member3 Regola n.3
        """

        config = await self.db.find_one({"_id": "config"})

        if config is None:
            return await ctx.send("Non c'è nessun canale dei log configurato.")
        else:
            channel = ctx.guild.get_channel(int(config["channel"]))

        if channel is None:
            await ctx.send("Non c'è nessun canale dei log configurato.")
            return

        try:
            for member in members:
                await member.kick(reason=f"{reason if reason else None}")
                embed = discord.Embed(
                    color=discord.Color.red(),
                    title=f"{member} è stato kickato!",
                    timestamp=datetime.datetime.utcnow(),
                )

                embed.add_field(
                    name="Moderatore", value=f"{ctx.author}", inline=False,
                )

                if reason is not None:
                    embed.add_field(name="Reason", value=reason, inline=False)

                await ctx.send(f"🦶 | {member} è stato kickato!")
                await channel.send(embed=embed)

        except discord.Forbidden:
            await ctx.send("Non ho i permessi per kickare gente.")

        except Exception as e:
            await ctx.send(
                "Piccolo errore, controlla i log di Heroku per maggiori informazioni."
            )
            logger.error(e)
            return

    @commands.command()
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def warn(self, ctx, member: discord.Member, *, reason: str):
        """Warna un membro.
        Usage:
        {prefix}warn @member testù
        """

        if member.bot:
            return await ctx.send("Non puoi warnare i miei fratelli bots.")

        channel_config = await self.db.find_one({"_id": "config"})

        if channel_config is None:
            return await ctx.send("Non c'è nessun canale dei log configurato.")
        else:
            channel = ctx.guild.get_channel(int(channel_config["channel"]))

        if channel is None:
            return

        config = await self.db.find_one({"_id": "warns"})

        if config is None:
            config = await self.db.insert_one({"_id": "warns"})

        try:
            userwarns = config[str(member.id)]
        except KeyError:
            userwarns = config[str(member.id)] = []

        if userwarns is None:
            userw = []
        else:
            userw = userwarns.copy()

        userw.append({"reason": reason, "mod": ctx.author.id})

        await self.db.find_one_and_update(
            {"_id": "warns"}, {"$set": {str(member.id): userw}}, upsert=True
        )

        await ctx.send(f"Warnato con successo **{member}**\n`{reason}`")

        await channel.send(
            embed=await self.generateWarnEmbed(
                str(member.id), str(ctx.author.id), len(userw), reason
            )
        )
        del userw
        return

    @commands.command()
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def pardon(self, ctx, member: discord.Member, *, reason: str):
        """Rimuovi tutti i warn di una persona.
        Usage:
        {prefix}pardon @member Bravo pampinoh.
        """

        if member.bot:
            return await ctx.send("I miei fratelli bots non possono essere warnati, quindi nemmeno perdonati.")

        channel_config = await self.db.find_one({"_id": "config"})

        if channel_config is None:
            return await ctx.send("Non c'è nessun canale dei log configurato.")
        else:
            channel = ctx.guild.get_channel(int(channel_config["channel"]))

        if channel is None:
            return

        config = await self.db.find_one({"_id": "warns"})

        if config is None:
            return

        try:
            userwarns = config[str(member.id)]
        except KeyError:
            return await ctx.send(f"{member} è un bravo ragazzo, non ha nemmeno un warn.")

        if userwarns is None:
            await ctx.send(f"{member} Non ha nemmeno un warn.")

        await self.db.find_one_and_update(
            {"_id": "warns"}, {"$set": {str(member.id): []}}
        )

        await ctx.send(f"Il boss perdona tutti, questa volta ha perdonato **{member}**\n`{reason}`")

        embed = discord.Embed(color=discord.Color.blue())

        embed.set_author(
            name=f"Pardon | {member}", icon_url=member.avatar_url,
        )
        embed.add_field(name="User", value=f"{member}")
        embed.add_field(
            name="Moderator", value=f"<@{ctx.author.id}> - `{ctx.author}`",
        )
        embed.add_field(name="Reason", value=reason)
        embed.add_field(name="Total Warnings", value="0")

        return await channel.send(embed=embed)

    async def generateWarnEmbed(self, memberid, modid, warning, reason):
        member: discord.User = await self.bot.fetch_user(int(memberid))
        mod: discord.User = await self.bot.fetch_user(int(modid))

        embed = discord.Embed(color=discord.Color.red())

        embed.set_author(
            name=f"Warn | {member}", icon_url=member.avatar_url,
        )
        embed.add_field(name="User", value=f"{member}")
        embed.add_field(name="Moderator", value=f"<@{modid}>` - ({mod})`")
        embed.add_field(name="Reason", value=reason)
        embed.add_field(name="Total Warnings", value=warning)
        return embed


def setup(bot):
    bot.add_cog(ModerationPlugin(bot))
