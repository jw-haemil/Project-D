import discord
from discord.ext import commands

import asyncio
import random

from src.classes import command_checks
from src.classes.bot import Bot, Cog
from src.classes.enums import fish_embed_color


class FishingButton(discord.ui.Button["FishingView"]):
    def __init__(self):
        super().__init__(label="낚싯대 들기", emoji="🎣", style=discord.ButtonStyle.gray)

    # 낚시 로직
    async def callback(self, interaction: discord.Interaction[Bot]):
        assert self.view is not None
        view = self.view

        if view.ctx.author != interaction.user: # 본인이 맞는지 확인
            return

        if interaction.user not in view.fishing_users: # 다른 플랫폼에서 동시에 누르는걸 방지
            return

        view.logic_task.cancel()
        view.fishing_users.remove(interaction.user)
        view.stop()

        embed = None
        match self.style:
            case discord.ButtonStyle.gray:
                content = "낚싯대를 너무 일찍 들어버렸다..."

            case discord.ButtonStyle.green:
                content = "물고기를 잡았다!"
                user_info = view.ctx.bot.database.get_user_info(interaction.user)
                fish_info = view.ctx.bot.database.get_fish_info()

                fish = await fish_info.get_random_fish()
                await user_info.add_money(fish.price)
                embed = discord.Embed(
                    title=f"{fish.name}",
                    description=f"{fish.description}",
                    colour=fish_embed_color[fish.rating]
                )
                embed.add_field(name="길이", value=f"{fish.length_str}")
                embed.add_field(name="가격", value=f"{fish.price:,}원")
                embed.add_field(name="등급", value=f"{fish.rating_str}")
            case _:
                return

        self.disabled = True
        assert self.disabled
        # interaction.response.edit_message를 사용하면 멘션이 풀리므로 아래와 같이 해결
        await interaction.message.edit(content=content, embed=embed, view=None if embed else view)
        assert self.disabled
        await interaction.response.defer()


class FishingView(discord.ui.View):
    def __init__(self, cog: "Fishing", context: commands.Context["Fishing"]):
        super().__init__(timeout=180)
        self.cog = cog
        self.ctx = context
        self.fishing_users = cog.fishing_users
        self.logic_task: asyncio.Task = None

        self.add_item(FishingButton())

    def start_logic(self, message: discord.Message):
        self.logic_task = asyncio.create_task(self.fishing_logic(message))

    async def fishing_logic(self, message: discord.Message):
        # 물고기가 걸리기끼지의 시간
        await asyncio.sleep(random.uniform(self.cog.bot_setting.fishing_random_min, self.cog.bot_setting.fishing_random_max))

        # 물고기가 걸렸을 때
        button: FishingButton = self.children[0]
        button.style = discord.ButtonStyle.green # 버튼 색상 변경
        await message.edit(content="무언가가 걸린것 같다!", view=self)

        # 물고기를 잡을 때
        await asyncio.sleep(self.cog.bot_setting.fishing_timeout) # 물고기가 걸려있는 시간

        # 물고기를 놓쳤을 때
        self.stop()
        button.style = discord.ButtonStyle.red
        button.disabled = True
        await message.edit(content="물고기를 놓쳐버렸다...", view=self)
        if self.ctx.author in self.fishing_users:
            self.fishing_users.remove(self.ctx.author) # 낚시 종료 처리

    async def on_error(self, interaction: discord.Interaction[discord.Client], error: Exception, item: FishingButton) -> None:
        if interaction.user in self.fishing_users:
            self.fishing_users.remove(interaction.user)
        item.disabled = True
        await interaction.response.edit_message(content="낚시하던중 오류가 발생하였습니다.", view=self)
        await super().on_error(interaction, error, item)


class Fishing(Cog):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.fishing_users: set[discord.Member] = set() # 낚시 유저 정보 저장

    @commands.command(
        name="낚시",
        aliases=["ㄴㅅ"],
        description="낚시를 합니다. 낚시도중 메시지가 바뀌었을 때, 반응을 누르면 물고기가 잡힙니다."
    )
    @command_checks.is_registered()
    async def fishing(self, ctx: commands.Context[Bot]):
        if ctx.author in self.fishing_users:
            await ctx.reply("이미 낚시중입니다.", delete_after=3)
            return

        self.fishing_users.add(ctx.author) # 낚시 시작 처리
        view = FishingView(self, ctx)
        message = await ctx.reply("낚시하는중...", view=view)
        view.start_logic(message)

    @fishing.error
    async def fishing_error(self, ctx: commands.Context[Bot], error: commands.CommandError):
        if ctx.author in self.fishing_users:
            self.fishing_users.remove(ctx.author)


async def setup(bot: Bot): # setup 함수로 명령어 추가
    await bot.add_cog(Fishing(bot))
