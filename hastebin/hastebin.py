import discord
import os
from discord import Embed
from discord.ext import commands

from json import JSONDecodeError
from aiohttp import ClientResponseError


class HastebinCog(commands.Cog):
    """
    Carica il tuo testo su hastebin con questo plugin! (plugin tradotto da [Italian Riky](https://github.com/Italian-Riky))
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def hastebin(self, ctx, *, message):
        """Carica il tuo testo su hastebin! (Plugin tradotto da [Italian Riky](https://github.com/Italian-Riky))"""
        haste_url = os.environ.get("HASTE_URL", "https://hasteb.in")

        try:
            async with self.bot.session.post(
                haste_url + "/documents", data=message
            ) as resp:
                key = (await resp.json())["key"]
                embed = Embed(
                    title="Il tuo file hastebin",
                    color=self.bot.main_color,
                    description=f"{haste_url}/" + key,
                )
        except (JSONDecodeError, ClientResponseError, IndexError):
            embed = Embed(
                color=self.bot.main_color,
                description="Bip, Bup, Qualcosa è andato storto. "
                "è impossibile caricare il tuo testo su hastebin.",
            )
            embed.set_footer(text="Hastebin Plugin")
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        async with self.bot.session.post(
            "https://counter.modmail-plugins.piyush.codes/api/instances/hastebin",
            json={"id": self.bot.user.id},
        ):
            print("Caricato sull'API del plugin")


def setup(bot):
    bot.add_cog(HastebinCog(bot))
