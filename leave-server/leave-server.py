import discord
from discord.ext import commands


class LeaveGuildPlugin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def leaveguild(self, ctx, guild_id: int):
        """
            Forza il tuo bot a uscire da un server. (Plugin tradotto da [Italian-Riky](https://github.com/Italian-Riky).)
        """
        try:
            await self.bot.get_guild(guild_id).leave()
            await ctx.send("Uscito!")
            return
        except:
            await ctx.send("Errore!")
            return

    @commands.Cog.listener()
    async def on_ready(self):
        async with self.bot.session.post(
            "https://counter.modmail-plugins.piyush.codes/api/instances/leaveserver",
            json={"id": self.bot.user.id},
        ):
            print("Postato sull'API del plugin.")


def setup(bot):
    bot.add_cog(LeaveGuildPlugin(bot))
