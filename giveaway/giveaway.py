import asyncio
import aiohttp
import discord
import math
import random
import time
from datetime import datetime
from discord.ext import commands

from core import checks
from core.models import PermissionLevel


class GiveawayPlugin(commands.Cog):
    """
    Fai dei fantastici giveaway con questo ~~fantastico~~ plugin! (Plugin tradotto da [Italian Riky](https://github.com/Italian-Riky))
    """

    def __init__(self, bot):
        self.bot: discord.Client = bot
        self.db = bot.plugin_db.get_partition(self)
        self.active_giveaways = {}
        asyncio.create_task(self._set_giveaways_from_db())

    async def _set_giveaways_from_db(self):
        config = await self.db.find_one({"_id": "config"})
        if config is None:
            await self.db.find_one_and_update(
                {"_id": "config"}, {"$set": {"giveaways": dict()}}, upsert=True,
            )

        for key, giveaway in config.get("giveaways", {}).items():
            if key in self.active_giveaways:
                continue
            self.active_giveaways[str(key)] = giveaway
            self.bot.loop.create_task(self._handle_giveaway(giveaway))

    async def _update_db(self):
        await self.db.find_one_and_update(
            {"_id": "config"},
            {"$set": {"giveaways": self.active_giveaways}},
            upsert=True,
        )

    async def _handle_giveaway(self, giveaway):
        if str(giveaway["message"]) not in self.active_giveaways:
            return

        async def get_random_user(users, _guild, _winners):
            rnd = random.choice(users)
            in_guild = _guild.get_member(rnd)
            if rnd in _winners or in_guild is None or in_guild.id == self.bot.user.id:
                idk = await get_random_user(users, _guild, _winners)
                return idk
            win = [] + _winners
            win.append(rnd)
            return win

        while True:
            if str(giveaway["message"]) not in self.active_giveaways:
                break
            channel: discord.TextChannel = self.bot.get_channel(
                int(giveaway["channel"])
            )
            if channel is None:
                try:
                    self.active_giveaways.pop(str(giveaway["message"]))
                    await self._update_db()
                except:
                    pass
                return
            message = await channel.fetch_message(giveaway["message"])
            if message is None or not message.embeds or message.embeds[0] is None:
                try:
                    self.active_giveaways.pop(str(giveaway["message"]))
                    await self._update_db()
                except:
                    pass
                return
            guild: discord.Guild = self.bot.get_guild(giveaway["guild"])
            g_time = giveaway["time"] - time.time()

            if g_time <= 0:
                if len(message.reactions) <= 0:
                    embed = message.embeds[0]
                    embed.description = (
                        f"è finito il giveaway!\n\nPurtroppo, nessuno ha partecipato :("
                    )
                    embed.set_footer(
                        text=f"{giveaway['winners']} {'winners' if giveaway['winners'] > 1 else 'winner'} | Ended at"
                    )
                    await message.edit(embed=embed)
                    break

                to_break = False

                for r in message.reactions:
                    if str(giveaway["message"]) not in self.active_giveaways:
                        break

                    if r.emoji == "🎉":
                        reactions = r
                        reacted_users = await reactions.users().flatten()
                        if len(reacted_users) <= 1:
                            embed = message.embeds[0]
                            embed.description = (
                                f"è finito il giveaway!\n\nPurtroppo, nessuno ha partecipato :("
                            )
                            embed.set_footer(
                                text=f"{giveaway['winners']} {'winners' if giveaway['winners'] > 1 else 'winner'} | "
                                f"Ended at"
                            )
                            await message.edit(embed=embed)
                            del guild, channel, reacted_users, embed
                            break

                        # -1 cuz 1 for self
                        if giveaway["winners"] > (len(reacted_users) - 1):
                            giveaway["winners"] = len(reacted_users) - 1

                        winners = []

                        for index in range(len(reacted_users)):
                            reacted_users[index] = reacted_users[index].id

                        for _ in range(giveaway["winners"]):
                            winners = await get_random_user(
                                reacted_users, guild, winners
                            )

                        embed = message.embeds[0]
                        winners_text = ""
                        for winner in winners:
                            winners_text += f"<@{winner}> "

                        embed.description = f"è finito il giveaway!\n\n**{'Winners' if giveaway['winners'] > 1 else 'Winner'}:** {winners_text} "
                        embed.set_footer(
                            text=f"{giveaway['winners']} {'winners' if giveaway['winners'] > 1 else 'winner'} | "
                            f"Ended at"
                        )
                        await message.edit(embed=embed)
                        await channel.send(
                            f"🎉 Congratulazioni {winners_text}, hai vinto **{giveaway['item']}**!"
                        )
                        try:
                            self.active_giveaways.pop(str(giveaway["message"]))
                            await self._update_db()
                        except:
                            pass
                        del winners_text, winners, guild, channel, reacted_users, embed
                        to_break = True
                        break

                if to_break:
                    break
            else:

                time_remaining = f"{math.floor(g_time // 86400)} Days, {math.floor(g_time // 3600 % 24)} Hours, {math.floor(g_time // 60 % 60)} Minutes, {math.floor(g_time % 60)} Seconds "

                embed = message.embeds[0]
                embed.description = (
                    f"Reagisci con 🎉 Per entrare nel giveaway!\n\n"
                    f"Tempo Rimanente: **{time_remaining}**"
                )
                await message.edit(embed=embed)
                del channel, guild
                await asyncio.sleep(
                    60 if g_time > 60 else (5 if g_time > 5 else g_time)
                )

        return

    @commands.group(
        name="giveaway",
        aliases=["g", "giveaways", "gaway", "givea"],
        invoke_without_command=True,
    )
    @commands.guild_only()
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def giveaway(self, ctx: commands.Context):
        """
        Crea / Ferma Giveaway!
        """
        await ctx.send_help(ctx.command)
        return

    @checks.has_permissions(PermissionLevel.ADMIN)
    @giveaway.command(name="start", aliases=["create", "c", "s"])
    async def start(self, ctx: commands.Context, channel: discord.TextChannel):
        """
        Fai partire un giveaway in modalità interattiva!
        """

        def check(msg: discord.Message):
            return (
                ctx.author == msg.author
                and ctx.channel == msg.channel
                and (len(msg.content) < 2048)
            )

        def cancel_check(msg: discord.Message):
            return msg.content == "cancel" or msg.content == f"{ctx.prefix}cancel"

        embed = discord.Embed(colour=0x00FF00)

        await ctx.send(embed=self.generate_embed("Qual'è il premio?"))
        giveaway_item = await self.bot.wait_for("message", check=check)
        if cancel_check(giveaway_item) is True:
            await ctx.send("Cancellato.")
            return
        embed.title = giveaway_item.content
        await ctx.send(
            embed=self.generate_embed("Quanti vincitori devono essere selezionati?")
        )
        giveaway_winners = await self.bot.wait_for("message", check=check)
        if cancel_check(giveaway_winners) is True:
            await ctx.send("Cancellato.")
            return
        try:
            giveaway_winners = int(giveaway_winners.content)
        except:
            await ctx.send(
                "incapace di analizzare i vincitori dell'omaggio in numeri, uscire. Assicurati di passare i numeri dal prossimo "
                "time"
            )
            return

        if giveaway_winners <= 0:
            await ctx.send(
                "Il giveaway può essere vinto solo da 1 o più persone. Annullamento del comando."
            )
            return

        await ctx.send(
            embed=self.generate_embed(
                "Quanto deve durare il giveaway?\n\n2d / 2days / 2day -> 2 days\n"
                "2m -> 2 minutes\n2 months -> 2 months"
                "\ntomorrow / in 10 minutes / 2h 10minutes work too\n"
            )
        )
        time_cancel = False
        while True:
            giveaway_time = await self.bot.wait_for("message", check=check)
            if cancel_check(giveaway_time) is True:
                time_cancel = True
                await ctx.send("Cancellato.")
                break
            resp = await self.bot.session.get(
                "https://dateparser.piyush.codes",
                params={"date": f"in {giveaway_time.content}"},
            )
            if resp.status == 400:
                await ctx.send(
                    "Non sono riuscito ad analizzare il tempo correttamente, riprova."
                )
                continue
            elif resp.status == 500:
                await ctx.send("L'API per le date sembra avere alcuni problemi.")
                time_cancel = True
                break
            else:
                json = await resp.json()
                giveaway_time = json["message"]
                break

        if time_cancel is True:
            return

        embed.description = (
            f"Reagisci con 🎉 Per entrare nel giveaway!\n\n"
            f"Tempo rimanente: **{datetime.fromtimestamp(giveaway_time).strftime('%d %H:%M:%S')}**"
        )
        embed.set_footer(
            text=f"{giveaway_winners} {'winners' if giveaway_winners > 1 else 'winner'} | Ends at"
        )
        embed.timestamp = datetime.fromtimestamp(giveaway_time)
        msg: discord.Message = await channel.send(embed=embed)
        await msg.add_reaction("🎉")
        giveaway_obj = {
            "item": giveaway_item.content,
            "winners": giveaway_winners,
            "time": giveaway_time,
            "guild": ctx.guild.id,
            "channel": channel.id,
            "message": msg.id,
        }
        self.active_giveaways[str(msg.id)] = giveaway_obj
        await ctx.send("Fatto!")
        await self._update_db()
        await self._start_new_giveaway_thread(giveaway_obj)

    @checks.has_permissions(PermissionLevel.ADMIN)
    @giveaway.command(name="reroll", aliases=["rroll"])
    async def reroll(self, ctx: commands.Context, _id: str, winners_count: int):
        """
        reroll

        **Uso:**
        {prefix}giveaway reroll <message_id> <winners_count>
        """

        # Don't roll if giveaway is active
        if _id in self.active_giveaways:
            await ctx.send("Scusa, Ma non puoi rerollare in un giveaway attivo.")
            return

        async def get_random_user(users, _guild, _winners):
            rnd = random.choice(users)
            in_guild = _guild.get_member(rnd)
            if rnd in _winners or in_guild is None or in_guild.id == self.bot.user.id:
                idk = await get_random_user(users, _guild, _winners)
                return idk
            win = [] + _winners
            win.append(rnd)
            return win

        try:
            message = await ctx.channel.fetch_message(int(_id))
        except discord.Forbidden:
            await ctx.send("Non ho i permessi per leggere la cronologia dei messaggi.")
            return
        except discord.NotFound:
            await ctx.send("Messaggio non trovato.")
            return

        if not message.embeds or message.embeds[0] is None:
            await ctx.send(
                "Il messaggio fornito non ha un incorporamento, quindi non è correlato a un giveaway."
            )
            return

        if len(message.reactions) <= 0:
            embed = message.embeds[0]
            embed.description = f"Il giveaway è concluso!\n\nPurtroppo nessuno ha partecipato :("
            embed.set_footer(
                text=f"{winners_count} {'winners' if winners_count > 1 else 'winner'} | Ended at"
            )
            await message.edit(embed=embed)
            return

        for r in message.reactions:
            if r.emoji == "🎉":
                reactions = r
                reacted_users = await reactions.users().flatten()
                if len(reacted_users) <= 1:
                    embed = message.embeds[0]
                    embed.description = (
                        f"Il giveaway è concluso!\n\nPurtroppo nessuno ha partecipato :("
                    )
                    await message.edit(embed=embed)
                    del reacted_users, embed
                    break

                # -1 cuz 1 for self
                if winners_count > (len(reacted_users) - 1):
                    winners_count = len(reacted_users) - 1

                winners = []

                for index in range(len(reacted_users)):
                    reacted_users[index] = reacted_users[index].id

                for _ in range(winners_count):
                    winners = await get_random_user(reacted_users, ctx.guild, winners)

                embed = message.embeds[0]
                winners_text = ""
                for winner in winners:
                    winners_text += f"<@{winner}> "

                embed.description = f"Il giveaway è concluso!\n\n**{'Winners' if winners_count > 1 else 'Winner'}:** {winners_text}"
                embed.set_footer(
                    text=f"{winners_count} {'winners' if winners_count > 1 else 'winner'} | Ended at"
                )
                await message.edit(embed=embed)
                await ctx.channel.send(
                    f"🎉 Congratulazioni {winners_text}, Hai vinto **{embed.title}**!"
                )
                del winners_text, winners, winners_count, reacted_users, embed
                break

    @giveaway.command(name="cancel", aliases=["stop"])
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def cancel(self, ctx: commands.Context, _id: str):
        """
        Ferma un giveaway

        **Uso:**
        {prefix}giveaway stop <message_id>
        """

        if _id not in self.active_giveaways:
            await ctx.send("Impossibile trovare un giveaway attivo nell'ID del messaggio!")
            return

        giveaway = self.active_giveaways[_id]
        channel: discord.TextChannel = self.bot.get_channel(int(giveaway["channel"]))
        try:
            message = await channel.fetch_message(int(_id))
        except discord.Forbidden:
            await ctx.send("Non ho i permessi di leggere la cronologia dei messaggi.")
            return
        except discord.NotFound:
            await ctx.send("Messaggio non trovato.")
            return

        if not message.embeds or message.embeds[0] is None:
            await ctx.send(
                "Il messaggio ricevuto non è un'embed, Quindi questo non è legato ad un giveaway."
            )
            return

        embed = message.embeds[0]
        embed.description = "Il giveaway è stato cancellato."
        await message.edit(embed=embed)
        self.active_giveaways.pop(_id)
        await self._update_db()
        await ctx.send("Cancellato!")
        return

    async def _start_new_giveaway_thread(self, obj):
        await self.bot.loop.create_task(self._handle_giveaway(obj))

    def generate_embed(self, description: str):
        embed = discord.Embed()
        embed.colour = self.bot.main_color
        embed.description = description

        return embed


def setup(bot):
    bot.add_cog(GiveawayPlugin(bot))
