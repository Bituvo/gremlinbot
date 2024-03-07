from discord import ui
from math import ceil
import discord
import data

class SetDescriptionModal(ui.Modal):
    def __init__(self, index, title="Gremlin Description"):
        super().__init__(title=title)
        self.index = index
        self.add_item(ui.TextInput(label="New description"))

    async def on_submit(self, interaction):
        data.candidates[self.index]["description"] = self.children[0].value
        data.save_data()

        try:
            await interaction.response.edit_message(
                content = f"Gremlin description set!",
                view = None
            )
        except discord.errors.NotFound:
            await interaction.response.send_message(
                f"Gremlin description set!",
                ephemeral = True
            )

class AddDescriptionView(ui.View):
    def __init__(self, index):
        super().__init__()
        self.index = index

    @ui.button(label="Add description", style=discord.ButtonStyle.primary)
    async def add_description(self, interaction, button):
        await interaction.response.send_modal(SetDescriptionModal(self.index))

class PaginatedCandidatesView(ui.View):
    def __init__(self):
        super().__init__()
        self.total_pages = ceil(len(data.candidates) / data.CANDIDATES_PER_PAGE)
        self.page = 1

    async def get_page(self):
        embed = discord.Embed(title=f"Gremlin Candidates ({len(data.candidates)})", color=data.ACCENT)
    
        start_index = (self.page - 1) * data.CANDIDATES_PER_PAGE
        candidates_to_show = data.candidates[start_index:start_index + data.CANDIDATES_PER_PAGE]

        for i, candidate in enumerate(candidates_to_show):
            name = candidate["description"] or "[No description given]"
            embed.add_field(
                name = f"`#{start_index + i + 1}`: *{name}* by __{candidate['author-name']}__",
                value = candidate["message-url"],
                inline = False
            )
        
        embed.set_footer(text=f"Page {self.page} / {self.total_pages}")

        return embed

    async def initial_page(self, interaction):
        embed = await self.get_page()
        await self.update_buttons()
        await interaction.response.send_message(embed=embed, view=self, ephemeral=True)

    async def refresh_page(self, interaction):
        embed = await self.get_page()
        await self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    async def update_buttons(self):
        self.children[0].disabled = self.page == 1
        self.children[1].disabled = self.page == 1
        self.children[2].disabled = self.page == self.total_pages
        self.children[3].disabled = self.page == self.total_pages

    @ui.button(emoji="⏮️", style=discord.ButtonStyle.primary)
    async def beginning(self, interaction, button):
        self.page = 1
        await self.refresh_page(interaction)

    @ui.button(emoji="◀️", style=discord.ButtonStyle.primary)
    async def previous(self, interaction, button):
        self.page -= 1
        await self.refresh_page(interaction)

    @ui.button(emoji="▶️", style=discord.ButtonStyle.primary)
    async def next(self, interaction, button):
        self.page += 1
        await self.refresh_page(interaction)

    @ui.button(emoji="⏭️", style=discord.ButtonStyle.primary)
    async def end(self, interaction, button):
        self.page = self.total_pages
        await self.refresh_page(interaction)

class ConfirmClearCandidatesView(ui.View):
    def __init__(self):
        super().__init__()
    
    @ui.button(label="Clear all candidates", style=discord.ButtonStyle.danger)
    async def clear_candidates(self, interaction, button):
        data.candidates = []
        data.save_data()

        await interaction.response.edit_message(content="Gremlin candidates cleared!", view=None)

    @ui.button(label="Cancel", style=discord.ButtonStyle.primary)
    async def cancel(self, interaction, button):
        await interaction.response.edit_message(content="Candidate deletion cancelled.", view=None)

class ConfirmClearElectedView(ui.View):
    def __init__(self):
        super().__init__()
    
    @ui.button(label="Clear elected list", style=discord.ButtonStyle.danger)
    async def clear_elected(self, interaction, button):
        data.elected_message_ids = []
        data.amount_elected = 0
        data.save_data()

        await interaction.response.edit_message(content="Elected gremlins cleared!", view=None)

    @ui.button(label="Cancel", style=discord.ButtonStyle.primary)
    async def cancel(self, interaction, button):
        await interaction.response.edit_message(content="Elected gremlin deletion cancelled.", view=None)
