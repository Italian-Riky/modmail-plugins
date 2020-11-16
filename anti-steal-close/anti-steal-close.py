import discord
from datetime import datetime
from discord.ext import commands

from core.time import UserFriendlyTime, human_timedelta
from core.models import PermissionLevel
from core import checks


class AntiStealClosePlugin(commands.Cog):
    """
    Un'iniziativa per impedire alla gente di rubare i thread chiusi.(Plugin tradotto da [Italian Riky](https://github.com/Italian-Riky))
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["asc", "notclosedbyme", "antisteal", "anti-steal"])
    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @checks.thread_only()
    async def anti_steal_close(self, ctx, user: discord.User, *, after: UserFriendlyTime = None):
        """
        Chiudi il thread per conto di un altro utente.

        **Usa:**
        [p]asc <persona> <opzioni regolari che passi al comando close>
        """
        thread = ctx.thread

        now = datetime.utcnow()

        close_after = (after.dt - now).total_seconds() if after else 0
        message = after.arg if after else None
        silent = str(message).lower() in {"silent", "silently"}
        cancel = str(message).lower() == "cancel"

        if cancel:

            if thread.close_task is not None or thread.auto_close_task is not None:
                await thread.cancel_closure(all=True)
                embed = discord.Embed(
                    color=self.bot.error_color,
                    description="La chiusura automatica è stata cancellata.",
                )
            else:
                embed = discord.Embed(
                    color=self.bot.error_color,
                    description="La chiusura di questo thread non è già stata pianificata.",
                )

            return await ctx.send(embed=embed)

        if after and after.dt > now:
            await self.send_scheduled_close_message(ctx, after, silent)

        dupe_message = ctx.message
        dupe_message.content = f"[Anti Close Steal] Il comando di chiusura del thread è stato richiamato da {ctx.author.name}#{ctx.author.discriminator}"

        await thread.note(dupe_message)

        await thread.close(
            closer=user, after=close_after, message=message, silent=silent
        )

    async def send_scheduled_close_message(self, ctx, after, silent=False):
        human_delta = human_timedelta(after.dt)

        silent = "*silently* " if silent else ""

        embed = discord.Embed(
            title="Chiusura automatica",
            description=f"Questo thread si chiuderà {silent}in {human_delta}.",
            color=self.bot.error_color,
        )

        if after.arg and not silent:
            embed.add_field(name="Message", value=after.arg)

        embed.set_footer(
            text="La chiusura sarà annullata " "se viene inviato un messaggio di thread."
        )
        embed.timestamp = after.dt

        await ctx.send(embed=embed)

    async def handle_log(self, guild: discord.Guild, ctx, user):
        channel = discord.utils.find(lambda c: "asc-logs" in c.topic, guild.channels)
        if channel is None:
            return
        else:
            embed = discord.Embed(
                color=self.bot.main_color
            )
            embed.description = f"Thread chiuso da {ctx.author.name}#{ctx.author.discriminator} per conto di {user.username}#{user.discriminator} "

            await channel.send(embed)


def setup(bot):
    bot.add_cog(AntiStealClosePlugin(bot))
