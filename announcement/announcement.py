import discord
import typing
import re
from discord.ext import commands

from core import checks
from core.models import PermissionLevel


class AnnoucementPlugin(commands.Cog):
    """
    Crea facilmente testo normale o annunci incorporati(Plugin tradotto da [Italian Riky](https://github.com/Italian-Riky))
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=["a"], invoke_without_command=True)
    @commands.guild_only()
    @checks.has_permissions(PermissionLevel.REGULAR)
    async def announcement(self, ctx: commands.Context):
        """
       Crea annunci facilmente
        """
        await ctx.send_help(ctx.command)

    @announcement.command()
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def start(self, ctx: commands.Context, role: typing.Optional[typing.Union[discord.Role, str]] = None):
        """
        Avvia una sessione interattiva per creare un annuncio
        Aggiungi il ruolo nel comando se desideri abilitare le menzioni

        **Esempio:**
        __ Annuncio con menzione del ruolo: __
        {prefix}announcement start everyone

        __ Annuncio senza menzione di ruolo__
        {prefix}announcement start
        """

        # TODO: Enable use of reactions
        def check(msg: discord.Message):
            return ctx.author == msg.author and ctx.channel == msg.channel

        # def check_reaction(reaction: discord.Reaction, user: discord.Member):
        #     return ctx.author == user and (str(reaction.emoji == "✅") or str(reaction.emoji) == "❌")

        def title_check(msg: discord.Message):
            return (
                ctx.author == msg.author
                and ctx.channel == msg.channel
                and (len(msg.content) < 256)
            )

        def description_check(msg: discord.Message):
            return (
                ctx.author == msg.author
                and ctx.channel == msg.channel
                and (len(msg.content) < 2048)
            )

        def footer_check(msg: discord.Message):
            return (
                ctx.author == msg.author
                and ctx.channel == msg.channel
                and (len(msg.content) < 2048)
            )

        # def author_check(msg: discord.Message):
        #     return (
        #             ctx.author == msg.author and ctx.channel == msg.channel and (len(msg.content) < 256)
        #     )

        def cancel_check(msg: discord.Message):
            if msg.content == "cancel" or msg.content == f"{ctx.prefix}cancel":
                return True
            else:
                return False

        if isinstance(role, discord.Role):
            role_mention = f"<@&{role.id}>"
            guild: discord.Guild = ctx.guild
            grole: discord.Role = guild.get_role(role.id)
            await grole.edit(mentionable=True)
        elif isinstance(role, str):
            if role == "here" or role == "@here":
                role_mention = "@here"
            elif role == "everyone" or role == "@everyone":
                role_mention = "@everyone"
        else:
            role_mention = ""

        await ctx.send("Avvio di un processo interattivo per creare un annuncio")

        await ctx.send(
            embed=await self.generate_embed("Vuoi un messaggio incorporato? `[y/n]`")
        )

        embed_res: discord.Message = await self.bot.wait_for("message", check=check)
        if cancel_check(embed_res) is True:
            await ctx.send("Cancellato!")
            return
        elif cancel_check(embed_res) is False and embed_res.content.lower() == "n":
            await ctx.send(
                embed=await self.generate_embed(
                    "Ok, facciamo un annuncio senza incorporamento."
                    "\nCos'è l'annuncio?"
                )
            )
            announcement = await self.bot.wait_for("message", check=check)
            if cancel_check(announcement) is True:
                await ctx.send("Cancellato!")
                return
            else:
                await ctx.send(
                    embed=await self.generate_embed(
                        "In quale canale devo mandare il messaggio?"
                    )
                )
                channel: discord.Message = await self.bot.wait_for(
                    "message", check=check
                )
                if cancel_check(channel) is True:
                    await ctx.send("Cancellato!")
                    return
                else:
                    if channel.channel_mentions[0] is None:
                        await ctx.send("Annullato perché non è stato fornito alcun canale")
                        return
                    else:
                        await channel.channel_mentions[0].send(
                            f"{role_mention}\n{announcement.content}"
                        )
        elif cancel_check(embed_res) is False and embed_res.content.lower() == "y":
            embed = discord.Embed()
            await ctx.send(
                embed=await self.generate_embed(
                    "L'incorporamento dovrebbe avere un titolo? `[y/n]`"
                )
            )
            t_res = await self.bot.wait_for("message", check=check)
            if cancel_check(t_res) is True:
                await ctx.send("Cancellato")
                return
            elif cancel_check(t_res) is False and t_res.content.lower() == "y":
                await ctx.send(
                    embed=await self.generate_embed(
                        "Quale dovrebbe essere il titolo dell'incorporamento?"
                        "\n**Non deve superare i 256 caratteri**"
                    )
                )
                tit = await self.bot.wait_for("message", check=title_check)
                embed.title = tit.content
            await ctx.send(
                embed=await self.generate_embed(
                    "L'incorporamento dovrebbe avere una descrizione?`[y/n]`"
                )
            )
            d_res: discord.Message = await self.bot.wait_for("message", check=check)
            if cancel_check(d_res) is True:
                await ctx.send("Cancellato")
                return
            elif cancel_check(d_res) is False and d_res.content.lower() == "y":
                await ctx.send(
                    embed=await self.generate_embed(
                        "Cosa vuoi come descrizione per l'incorporamento?"
                        "\n**Non deve superare i 2048 caratteri**"
                    )
                )
                des = await self.bot.wait_for("message", check=description_check)
                embed.description = des.content

            await ctx.send(
                embed=await self.generate_embed(
                    "L'incorporamento dovrebbe avere una miniatura?`[y/n]`"
                )
            )
            th_res: discord.Message = await self.bot.wait_for("message", check=check)
            if cancel_check(th_res) is True:
                await ctx.send("Cancellato")
                return
            elif cancel_check(th_res) is False and th_res.content.lower() == "y":
                await ctx.send(
                    embed=await self.generate_embed(
                        "Qual è la miniatura dell'incorporamento? Inserisci un "" URL valido "
                    )
                )
                thu = await self.bot.wait_for("message", check=check)
                embed.set_thumbnail(url=thu.content)

            await ctx.send(
                embed=await self.generate_embed("L'incorporamento dovrebbe avere un'immagine?`[y/n]`")
            )
            i_res: discord.Message = await self.bot.wait_for("message", check=check)
            if cancel_check(i_res) is True:
                await ctx.send("Cancellato")
                return
            elif cancel_check(i_res) is False and i_res.content.lower() == "y":
                await ctx.send(
                    embed=await self.generate_embed(
                        "Qual è l'immagine dell'incorporamento? Inserisci un "" URL valido "
                    )
                )
                i = await self.bot.wait_for("message", check=check)
                embed.set_image(url=i.content)

            await ctx.send(
                embed=await self.generate_embed("L'incorporamento avrà un piè di pagina?`[y/n]`")
            )
            f_res: discord.Message = await self.bot.wait_for("message", check=check)
            if cancel_check(f_res) is True:
                await ctx.send("Cancellato")
                return
            elif cancel_check(f_res) is False and f_res.content.lower() == "y":
                await ctx.send(
                    embed=await self.generate_embed(
                        "Quale vuoi che sia il piè di pagina dell'incorporamento?"
                        "\n**Non deve superare i 2048 caratteri**"
                    )
                )
                foo = await self.bot.wait_for("message", check=footer_check)
                embed.set_footer(text=foo.content)

            await ctx.send(
                embed=await self.generate_embed(
                    "Vuoi che abbia un colore?`[y/n]`"
                )
            )
            c_res: discord.Message = await self.bot.wait_for("message", check=check)
            if cancel_check(c_res) is True:
                await ctx.send("Cancellato!")
                return
            elif cancel_check(c_res) is False and c_res.content.lower() == "y":
                await ctx.send(
                    embed=await self.generate_embed(
                        "Di che colore dovrebbe avere l'incorporamento? "
                        "Fornisci un colore esadecimale valido"
                    )
                )
                colo = await self.bot.wait_for("message", check=check)
                if cancel_check(colo) is True:
                    await ctx.send("Cancellato!")
                    return
                else:
                    match = re.search(
                        r"^#(?:[0-9a-fA-F]{3}){1,2}$", colo.content
                    )  # uwu thanks stackoverflow
                    if match:
                        embed.colour = int(
                            colo.content.replace("#", "0x"), 0
                        )  # Basic Computer Science
                    else:
                        await ctx.send(
                            "Fallito! Non è un colore esadecimale valido, ottieni il tuo da "
                            "https://www.google.com/search?q=color+picker"
                        )
                        return

            await ctx.send(
                embed=await self.generate_embed(
                    "I che canale devo mandare l'annuncio? )
            channel: discord.Message = await self.bot.wait_for("message", check=check)
            if cancel_check(channel) is True:
                await ctx.send("Cancellato!")
                return
            else:
                if channel.channel_mentions[0] is None:
                    await ctx.send("Cancellato perchè non è stato dato nessun canale")
                    return
                else:
                    schan = channel.channel_mentions[0]
            await ctx.send(
                "Ecco il messaggio incorporato, lo invio? `[y/n]`", embed=embed
            )
            s_res = await self.bot.wait_for("message", check=check)
            if cancel_check(s_res) is True or s_res.content.lower() == "n":
                await ctx.send("Cancellato!")
                return
            else:
                await schan.send(f"{role_mention}", embed=embed)
        if isinstance(role, discord.Role):
            guild: discord.Guild = ctx.guild
            grole: discord.Role = guild.get_role(role.id)
            if grole.mentionable is True:
                await grole.edit(mentionable=False)

    @announcement.command(aliases=["native", "n", "q"])
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def quick(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel,
        role: typing.Optional[typing.Union[discord.Role, str]],
        *,
        msg: str,
    ):
        """
        Un vecchio metodo per creare i messaggi

        **Uso:**
        {prefix}announcement quick #canale <Ruolo OPZIONALE> messaggio
        """
        if isinstance(role, discord.Role):
            guild: discord.Guild = ctx.guild
            grole: discord.Role = guild.get_role(role.id)
            await grole.edit(mentionable=True)
            role_mention = f"<@&{role.id}>"
        elif isinstance(role, str):
            if role == "here" or role == "@here":
                role_mention = "@here"
            elif role == "everyone" or role == "@everyone":
                role_mention = "@everyone"
            else:
                msg = f"{role} {msg}"
                role_mention = ""

        await channel.send(f"{role_mention}\n{msg}")
        await ctx.send("Done")

        if isinstance(role, discord.Role):
            guild: discord.Guild = ctx.guild
            grole: discord.Role = guild.get_role(role.id)
            if grole.mentionable is True:
                await grole.edit(mentionable=False)

    @commands.Cog.listener()
    async def on_ready(self):
        async with self.bot.session.post(
            "https://counter.modmail-plugins.piyush.codes/api/instances/announcement",
            json={"id": self.bot.user.id},
        ):
            print("Postato sull'API del plugin")

    @staticmethod
    async def generate_embed(description: str):
        embed = discord.Embed()
        embed.colour = discord.Colour.blurple()
        embed.description = description

        return embed


def setup(bot):
    bot.add_cog(AnnoucementPlugin(bot))
