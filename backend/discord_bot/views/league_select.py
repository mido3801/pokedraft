"""League selection views for Discord bot."""
import discord
from typing import Callable, Awaitable, Optional

from discord_bot.config import Colors, Timeouts


class LeagueSelectView(discord.ui.View):
    """A view with a dropdown to select a league."""

    def __init__(
        self,
        leagues: list,
        callback: Callable[[discord.Interaction, str], Awaitable[None]],
        placeholder: str = "Select a league...",
        timeout: float = Timeouts.LEAGUE_SELECT_VIEW,
    ):
        """Initialize the league select view.

        Args:
            leagues: List of League objects to display.
            callback: Async function to call when a league is selected.
                      Receives (interaction, league_id).
            placeholder: Placeholder text for the dropdown.
            timeout: View timeout in seconds.
        """
        super().__init__(timeout=timeout)
        self.callback = callback
        self.selected_league_id: Optional[str] = None

        # Create the select menu
        select = LeagueSelect(
            leagues=leagues,
            placeholder=placeholder,
            callback=self._handle_select,
        )
        self.add_item(select)

    async def _handle_select(
        self, interaction: discord.Interaction, league_id: str
    ) -> None:
        """Handle league selection."""
        self.selected_league_id = league_id
        await self.callback(interaction, league_id)
        self.stop()

    async def on_timeout(self) -> None:
        """Handle view timeout."""
        # Disable all items
        for item in self.children:
            if isinstance(item, discord.ui.Select):
                item.disabled = True


class LeagueSelect(discord.ui.Select):
    """A select menu for choosing a league."""

    def __init__(
        self,
        leagues: list,
        callback: Callable[[discord.Interaction, str], Awaitable[None]],
        placeholder: str = "Select a league...",
    ):
        """Initialize the league select.

        Args:
            leagues: List of League objects.
            callback: Callback function.
            placeholder: Placeholder text.
        """
        self._callback = callback

        options = [
            discord.SelectOption(
                label=league.name[:100],
                value=str(league.id),
                description=f"Owner: {league.owner.display_name}"[:100]
                if league.owner
                else None,
            )
            for league in leagues[:25]  # Discord limit
        ]

        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle selection."""
        league_id = self.values[0]
        await self._callback(interaction, league_id)


class LeaguePromptView(discord.ui.View):
    """A view that prompts the user to select from their leagues."""

    def __init__(
        self,
        leagues: list,
        title: str = "Select a League",
        description: str = "Please select which league you want to use:",
        timeout: float = Timeouts.LEAGUE_SELECT_VIEW,
    ):
        """Initialize the prompt view.

        Args:
            leagues: List of League objects.
            title: Embed title.
            description: Embed description.
            timeout: View timeout.
        """
        super().__init__(timeout=timeout)
        self.leagues = leagues
        self.title = title
        self.description = description
        self.selected_league = None
        self.interaction: Optional[discord.Interaction] = None

        # Create the select menu
        options = [
            discord.SelectOption(
                label=league.name[:100],
                value=str(league.id),
                description=f"Owner: {league.owner.display_name}"[:100]
                if league.owner
                else None,
            )
            for league in leagues[:25]
        ]

        select = discord.ui.Select(
            placeholder="Select a league...",
            options=options,
        )
        select.callback = self._on_select
        self.add_item(select)

    def get_embed(self) -> discord.Embed:
        """Get the embed for the prompt."""
        return discord.Embed(
            title=self.title,
            description=self.description,
            color=Colors.INFO,
        )

    async def _on_select(self, interaction: discord.Interaction) -> None:
        """Handle league selection."""
        league_id = interaction.data["values"][0]
        self.selected_league = next(
            (lg for lg in self.leagues if str(lg.id) == league_id), None
        )
        self.interaction = interaction
        self.stop()

    async def on_timeout(self) -> None:
        """Handle timeout."""
        for item in self.children:
            if isinstance(item, discord.ui.Select):
                item.disabled = True


async def prompt_league_selection(
    interaction: discord.Interaction,
    leagues: list,
    title: str = "Select a League",
    description: str = "Please select which league you want to use:",
    ephemeral: bool = True,
) -> Optional[tuple]:
    """Prompt the user to select a league.

    Args:
        interaction: The Discord interaction.
        leagues: List of leagues to choose from.
        title: Prompt title.
        description: Prompt description.
        ephemeral: Whether to send as ephemeral message.

    Returns:
        Tuple of (selected_league, new_interaction) or None if timed out.
    """
    if not leagues:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="No Leagues Found",
                description="You don't have any leagues to select from.",
                color=Colors.ERROR,
            ),
            ephemeral=ephemeral,
        )
        return None

    if len(leagues) == 1:
        # Auto-select the only league
        return (leagues[0], interaction)

    view = LeaguePromptView(
        leagues=leagues,
        title=title,
        description=description,
    )

    await interaction.response.send_message(
        embed=view.get_embed(),
        view=view,
        ephemeral=ephemeral,
    )

    await view.wait()

    if view.selected_league and view.interaction:
        return (view.selected_league, view.interaction)

    return None
