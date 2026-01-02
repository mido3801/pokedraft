"""Confirmation views for Discord bot."""
import discord
from typing import Callable, Awaitable, Optional
from enum import Enum

from discord_bot.config import Colors, Timeouts


class ConfirmationResult(str, Enum):
    """Result of a confirmation dialog."""

    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ConfirmationView(discord.ui.View):
    """A view with Confirm and Cancel buttons."""

    def __init__(
        self,
        confirm_label: str = "Confirm",
        cancel_label: str = "Cancel",
        confirm_style: discord.ButtonStyle = discord.ButtonStyle.success,
        cancel_style: discord.ButtonStyle = discord.ButtonStyle.danger,
        timeout: float = Timeouts.CONFIRMATION_VIEW,
    ):
        """Initialize the confirmation view.

        Args:
            confirm_label: Label for the confirm button.
            cancel_label: Label for the cancel button.
            confirm_style: Style for the confirm button.
            cancel_style: Style for the cancel button.
            timeout: View timeout in seconds.
        """
        super().__init__(timeout=timeout)
        self.result: ConfirmationResult = ConfirmationResult.TIMEOUT
        self.interaction: Optional[discord.Interaction] = None

        # Create buttons
        self.confirm_button = discord.ui.Button(
            label=confirm_label,
            style=confirm_style,
            custom_id="confirm",
        )
        self.confirm_button.callback = self._on_confirm

        self.cancel_button = discord.ui.Button(
            label=cancel_label,
            style=cancel_style,
            custom_id="cancel",
        )
        self.cancel_button.callback = self._on_cancel

        self.add_item(self.confirm_button)
        self.add_item(self.cancel_button)

    async def _on_confirm(self, interaction: discord.Interaction) -> None:
        """Handle confirm button click."""
        self.result = ConfirmationResult.CONFIRMED
        self.interaction = interaction
        self._disable_buttons()
        self.stop()

    async def _on_cancel(self, interaction: discord.Interaction) -> None:
        """Handle cancel button click."""
        self.result = ConfirmationResult.CANCELLED
        self.interaction = interaction
        self._disable_buttons()
        self.stop()

    def _disable_buttons(self) -> None:
        """Disable all buttons."""
        self.confirm_button.disabled = True
        self.cancel_button.disabled = True

    async def on_timeout(self) -> None:
        """Handle view timeout."""
        self.result = ConfirmationResult.TIMEOUT
        self._disable_buttons()


class ConfirmationEmbed:
    """Helper for creating confirmation embeds."""

    @staticmethod
    def create(
        title: str,
        description: str,
        fields: Optional[list[tuple[str, str, bool]]] = None,
        footer: Optional[str] = None,
        color: int = Colors.WARNING,
    ) -> discord.Embed:
        """Create a confirmation embed.

        Args:
            title: Embed title.
            description: Embed description.
            fields: List of (name, value, inline) tuples.
            footer: Optional footer text.
            color: Embed color.

        Returns:
            The created embed.
        """
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
        )

        if fields:
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)

        if footer:
            embed.set_footer(text=footer)
        else:
            embed.set_footer(text="This request will timeout in 5 minutes")

        return embed


async def confirm_action(
    interaction: discord.Interaction,
    title: str,
    description: str,
    fields: Optional[list[tuple[str, str, bool]]] = None,
    confirm_label: str = "Confirm",
    cancel_label: str = "Cancel",
    ephemeral: bool = True,
    timeout: float = Timeouts.CONFIRMATION_VIEW,
) -> tuple[ConfirmationResult, Optional[discord.Interaction]]:
    """Show a confirmation dialog and wait for response.

    Args:
        interaction: The original Discord interaction.
        title: Confirmation title.
        description: Confirmation description.
        fields: Optional embed fields.
        confirm_label: Confirm button label.
        cancel_label: Cancel button label.
        ephemeral: Whether to send as ephemeral message.
        timeout: Timeout in seconds.

    Returns:
        Tuple of (result, new_interaction).
    """
    embed = ConfirmationEmbed.create(
        title=title,
        description=description,
        fields=fields,
    )

    view = ConfirmationView(
        confirm_label=confirm_label,
        cancel_label=cancel_label,
        timeout=timeout,
    )

    await interaction.response.send_message(
        embed=embed,
        view=view,
        ephemeral=ephemeral,
    )

    await view.wait()

    return (view.result, view.interaction)


class DangerConfirmationView(ConfirmationView):
    """A confirmation view for dangerous actions requiring typed confirmation."""

    def __init__(
        self,
        confirmation_text: str,
        timeout: float = Timeouts.CONFIRMATION_VIEW,
    ):
        """Initialize the danger confirmation view.

        Args:
            confirmation_text: Text the user must type to confirm.
            timeout: View timeout.
        """
        super().__init__(
            confirm_label="I understand, proceed",
            cancel_label="Cancel",
            confirm_style=discord.ButtonStyle.danger,
            timeout=timeout,
        )
        self.confirmation_text = confirmation_text
        self.confirmed_text: Optional[str] = None

    async def _on_confirm(self, interaction: discord.Interaction) -> None:
        """Handle confirm - show modal for text confirmation."""
        modal = ConfirmationModal(self.confirmation_text)
        await interaction.response.send_modal(modal)
        await modal.wait()

        if modal.confirmed:
            self.result = ConfirmationResult.CONFIRMED
            self.interaction = modal.interaction
        else:
            self.result = ConfirmationResult.CANCELLED
            self.interaction = modal.interaction

        self._disable_buttons()
        self.stop()


class ConfirmationModal(discord.ui.Modal):
    """Modal for typed confirmation."""

    def __init__(self, confirmation_text: str):
        """Initialize the modal.

        Args:
            confirmation_text: Text user must type to confirm.
        """
        super().__init__(title="Confirm Action")
        self.confirmation_text = confirmation_text
        self.confirmed = False
        self.interaction: Optional[discord.Interaction] = None

        self.text_input = discord.ui.TextInput(
            label=f'Type "{confirmation_text}" to confirm',
            placeholder=confirmation_text,
            required=True,
            max_length=100,
        )
        self.add_item(self.text_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Handle modal submission."""
        self.interaction = interaction
        if self.text_input.value.strip().lower() == self.confirmation_text.lower():
            self.confirmed = True
            await interaction.response.send_message(
                "Action confirmed.", ephemeral=True
            )
        else:
            self.confirmed = False
            await interaction.response.send_message(
                "Confirmation text did not match. Action cancelled.",
                ephemeral=True,
            )
        self.stop()
