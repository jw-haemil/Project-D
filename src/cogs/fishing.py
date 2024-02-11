import discord
from discord.ext import commands

import asyncio
import random

from src.classes.bot import Bot, Cog
from src.classes.command_checks import Checks
from src.classes.enums import fish_embed_color


class FishingButton(discord.ui.View):
    def __init__(self, context: commands.Context[Bot], fishing_users: set):
        self.ctx = context
        self.fishing_users = fishing_users
        super().__init__()

    @discord.ui.button(label="낚싯대 들기", emoji="🎣", style=discord.ButtonStyle.gray)
    async def button_callback(self, interaction: discord.Interaction[Bot], button: discord.ui.Button):
        if self.ctx.author != interaction.user: # 본인이 맞는지 확인
            return

        self.fishing_users.remove(interaction.user)

        message = None
        embed = None
        if button.style == discord.ButtonStyle.gray:
            message = "낚싯대를 너무 일찍 들어버렸다..."

        elif button.style == discord.ButtonStyle.green:
            message = "물고기를 잡았다!"
            user_info = self.ctx.bot.database.get_user_info(self.ctx.author.id)
            fish_info = self.ctx.bot.database.get_fish_info()

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

        button.disabled = True
        # interaction.response.edit_message로 수정하면 멘션이 풀리므로 아래와 같이 해결
        await interaction.message.edit(content=message, embed=embed, view=None if embed else self)
        await interaction.response.defer()
        self.stop() # 뷰 무효화

    async def on_error(self, interaction: discord.Interaction[Bot], error: Exception, item: discord.ui.Button) -> None:
        if interaction.user in self.fishing_users:
            self.fishing_users.remove(interaction.user)
        item.disabled = True
        await interaction.response.edit_message(content="낚시하던중 오류가 발생하였습니다.", view=self)
        await super().on_error(interaction, error, item)


class Fishing(Cog):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.fishing_users = set() # 낚시 유저 정보 저장

    def add_fishing_user(self, user: discord.Member):
        """낚시 유저 정보 저장"""
        self.fishing_users.add(user)

    def remove_fishing_user(self, user: discord.Member):
        """낚시 유저 정보 삭제"""
        self.fishing_users.remove(user)

    def is_fishing_user(self, user: discord.Member):
        """낚시중인 유저인지 확인"""
        return user in self.fishing_users


    @commands.command(
        name="낚시",
        aliases=["ㄴㅅ"],
        description="낚시를 합니다. 낚시도중 메시지가 바뀌었을 때, 반응을 누르면 물고기가 잡힙니다."
    )
    @Checks.is_registered()
    async def fishing(self, ctx: commands.Context[Bot]):
        if self.is_fishing_user(ctx.author):
            await ctx.reply("이미 낚시중입니다.", delete_after=3)
            return

        self.add_fishing_user(ctx.author) # 낚시 시작 처리

        view = FishingButton(ctx, self.fishing_users) # 버튼 생성
        button: discord.ui.Button = view.children[0]
        message = await ctx.reply("낚시하는중...", view=view)

        await asyncio.sleep(random.randint(self.bot_setting.fishing_random_min, self.bot_setting.fishing_random_max)) # 낚는 시간
        if button.disabled == True: # sleep중 버튼을 눌렀을 때
            return

        button.style = discord.ButtonStyle.green # 버튼 색상 변경
        await message.edit(content="무언가가 걸린것 같다!", view=view)

        await asyncio.sleep(self.bot_setting.fishing_timeout) # 물고기 잡혀있는 시간
        if button.disabled == True: # sleep중 버튼을 눌렀을 때
            return

        button.disabled = True # 버튼 비활성화
        button.style = discord.ButtonStyle.red
        await message.edit(content="물고기를 놓쳐버렸다...", view=view)
        view.stop() # 뷰 무효화
        if ctx.author in self.fishing_users:
            self.remove_fishing_user(ctx.author) # 낚시 종료 처리

    @fishing.error
    async def fishing_error(self, ctx: commands.Context[Bot], error: commands.CommandError):
        if ctx.author in self.fishing_users:
            self.remove_fishing_user(ctx.author)


async def setup(bot: Bot): # setup 함수로 명령어 추가
    await bot.add_cog(Fishing(bot))