import discord
from datetime import datetime
from discord.ext import commands

from core import checks
from core.models import PermissionLevel


class TagsPlugin(commands.Cog):
    """
    Crea i tuoi fantastici tag per le tue fantastiche meme! (plugin tradotto da [Italian Riky](https://github.com/Italian-Riky))
    """
    def __init__(self, bot):
        self.bot: discord.Client = bot
        self.db = bot.plugin_db.get_partition(self)

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    @checks.has_permissions(PermissionLevel.REGULAR)
    async def tags(self, ctx: commands.Context):
        """
        Crea, edita & Gestisci Tags.
        """
        await ctx.send_help(ctx.command)

    @tags.command()
    async def add(self, ctx: commands.Context, name: str, *, content: str):
        """
        Crea un nuovo tag.
        """
        if (await self.find_db(name=name)) is not None:
            await ctx.send(f":x: | Un tag chiamato `{name}` Gia esiste!!")
            return
        else:
            ctx.message.content = content
            await self.db.insert_one(
                {
                    "name": name,
                    "content": ctx.message.clean_content,
                    "createdAt": datetime.utcnow(),
                    "updatedAt": datetime.utcnow(),
                    "author": ctx.author.id,
                    "uses": 0,
                }
            )

            await ctx.send
                f":white_check_mark: | Il tag `{name}` è stato creato!"
            )
            return

    @tags.command()
    async def edit(self, ctx: commands.Context, name: str, *, content: str):
        """
        Modifica un tag gia esistente!

        Solo l'owner del tag e i membri con il permesso di gestire il server possono usare questo comando.
        """
        tag = await self.find_db(name=name)

        if tag is None:
            await ctx.send(f":x: | Un tag chiamato `{name}` Non esiste")
            return
        else:
            member: discord.Member = ctx.author
            if ctx.author.id == tag["author"] or member.guild_permissions.manage_guild:
                await self.db.find_one_and_update(
                    {"name": name},
                    {"$set": {"content": content, "updatedAt": datetime.utcnow()}},
                )

                await ctx.send(
                    f":white_check_mark: | Il tag `{name}` è stato aggiornato correttamente!"
                )
            else:
                await ctx.send("Non hai il permesso di modificare questo tag.")

    @tags.command()
    async def delete(self, ctx: commands.Context, name: str):
        """
        Elimina un tag.

        Solo il proprietario del tag o i membri con il permesso di Gestire il Server possono usare questo comando.
        """
        tag = await self.find_db(name=name)
        if tag is None:
            await ctx.send(":x: | Il Tag `{name}` Non è stato trovato nel database, prova un'altro nome.")
        else:
            if (
                ctx.author.id == tag["author"]
                or ctx.author.guild_permissions.manage_guild
            ):
                await self.db.delete_one({"name": name})

                await ctx.send(
                    f":white_check_mark: | Il Tag `{name}` è stato eliminato con successo!"
                )
            else:
                await ctx.send("Non hai il permesso di eliminare questo tag")

    @tags.command()
    async def claim(self, ctx: commands.Context, name: str):
        """
        Reclama un tag quando il proprietario esce dal server!
        """
        tag = await self.find_db(name=name)

        if tag is None:
            await ctx.send(":x: | Il tag `{name}` Non è stato trovato.")
        else:
            member = await ctx.guild.get_member(tag["author"])
            if member is not None:
                await ctx.send(
                    f":x: | Il proprietario del tag è ancora nel server! `{member.name}#{member.discriminator}`"
                )
                return
            else:
                await self.db.find_one_and_update(
                    {"name": name},
                    {"$set": {"author": ctx.author.id, "updatedAt": datetime.utcnow()}},
                )

                await ctx.send(
                    f":white_check_mark: | Il tag `{name}` è ora di `{ctx.author.name}#{ctx.author.discriminator}`"
                )

    @tags.command()
    async def info(self, ctx: commands.Context, name: str):
        """
        Raccogli informazioni su un tag.
        """
        tag = await self.find_db(name=name)

        if tag is None:
            await ctx.send(":x: | Il tag `{name}` Non è stato trovato.")
        else:
            user: discord.User = await self.bot.fetch_user(tag["author"])
            embed = discord.Embed()
            embed.colour = discord.Colour.green()
            embed.title = f"Info sul tag{name}"
            embed.add_field(
                name="Creato da", value=f"{user.name}#{user.discriminator}"
            )
            embed.add_field(name="Creato il", value=tag["createdAt"])
            embed.add_field(
                name="Ultima modifica", value=tag["updatedAt"], inline=False
            )
            embed.add_field(name="Usi", value=tag["uses"], inline=False)
            await ctx.send(embed=embed)
            return

    @commands.command()
    async def tag(self, ctx: commands.Context, name: str):
        """
        Usa un tag!
        """
        tag = await self.find_db(name=name)
        if tag is None:
            await ctx.send(f":x: | il tag {name} Non è stato trovato.")
            return
        else:
            await ctx.send(tag["content"])
            await self.db.find_one_and_update(
                {"name": name}, {"$set": {"uses": tag["uses"] + 1}}
            )
            return

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if not msg.content.startswith(self.bot.prefix) or msg.author.bot:
            return
        content = msg.content.replace(self.bot.prefix, "")
        names = content.split(" ")

        tag = await self.db.find_one({"name": names[0]})

        if tag is None:
            return
        else:
            await msg.channel.send(tag["content"])
            await self.db.find_one_and_update(
                {"name": names[0]}, {"$set": {"uses": tag["uses"] + 1}}
            )
            return

    async def find_db(self, name: str):
        return await self.db.find_one({"name": name})


def setup(bot):
    bot.add_cog(TagsPlugin(bot))
