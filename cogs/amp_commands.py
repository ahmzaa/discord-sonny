from discord.ext import commands
from amp_handler import AMPManager


class AMPCommands(commands.Cog):
    def __init(self, bot):
        self.bot = bot
        self.amp = AMPManager()

    # Instance status
    @commands.command(name="status")
    async def status(self, ctx, *, server_name: str):
        data = await self.amp.get_server_info(server_name)

        if data:
            await ctx.send(
                f"**{data['name']}**\n"
                f"Status: {data['state']}\n"
                f"CPU: {data['cpu']}%\n"
                f"RAM: {data['ram']}%"
            )
        else:
            await ctx.send(f"Server `{server_name}` not found.")

    # Instance Power commands
    @commands.command(name="power")
    @commands.has_permissions(administrator=True)  # For security
    async def power(self, ctx, action: str, *, server_name: str):
        action = action.lower()

        async with ctx.typing():
            success, message = await self.amp.change_power_state(server_name, action)

        if success:
            await ctx.send(f"{message}")
        else:
            await ctx.send(f"{message}")


async def setup(bot):
    await bot.add_cog(AMPCommands(bot))
