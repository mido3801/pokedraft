"""Account management commands for Discord bot."""
import discord
from discord.ext import commands
from discord import app_commands

from discord_bot.cogs.base import BaseCog
from discord_bot.config import Colors, get_app_url
from discord_bot.database import get_db_session
from discord_bot.services.user_service import UserService


class AccountCommands(BaseCog):
    """Commands for managing account linking and settings."""

    account_group = app_commands.Group(
        name="account",
        description="Manage your PokeDraft account",
    )

    @account_group.command(name="link", description="Link your Discord account to PokeDraft")
    async def link(self, interaction: discord.Interaction):
        """Generate a link to connect Discord to PokeDraft account."""
        # Check if already linked
        async with get_db_session() as db:
            user_service = UserService(db)
            existing_user = await user_service.get_user_by_discord_id(
                str(interaction.user.id)
            )

            if existing_user:
                await interaction.response.send_message(
                    embed=self.info_embed(
                        "Already Linked",
                        f"Your Discord account is already linked to **{existing_user.display_name}**.\n\n"
                        "Use `/account info` to see your account details or "
                        "`/account unlink` to disconnect.",
                    ),
                    ephemeral=True,
                )
                return

        # Generate OAuth link
        oauth_url = get_app_url("/auth/discord")

        embed = discord.Embed(
            title="Link Your Account",
            description=(
                "To link your Discord account to PokeDraft:\n\n"
                f"1. [Click here to link]({oauth_url})\n"
                "2. Log in to your PokeDraft account\n"
                "3. Authorize the Discord connection\n\n"
                "Once linked, you can use all Discord commands!"
            ),
            color=Colors.PRIMARY,
        )
        embed.set_footer(text="Your Discord ID will be securely stored")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @account_group.command(name="info", description="View your linked account info")
    async def info(self, interaction: discord.Interaction):
        """Show information about the linked account."""
        async with get_db_session() as db:
            user_service = UserService(db)
            user = await user_service.get_user_by_discord_id(str(interaction.user.id))

            if not user:
                await interaction.response.send_message(
                    embed=self.error_embed(
                        "Account Not Linked",
                        "Your Discord account isn't linked to PokeDraft yet.\n"
                        "Use `/account link` to get started.",
                    ),
                    ephemeral=True,
                )
                return

            # Get notification settings
            settings = await user_service.get_notification_settings(str(user.id))

            embed = discord.Embed(
                title="Account Info",
                color=Colors.INFO,
            )
            embed.add_field(name="Display Name", value=user.display_name, inline=True)
            embed.add_field(name="Email", value=user.email, inline=True)
            embed.add_field(
                name="Member Since",
                value=user.created_at.strftime("%B %d, %Y"),
                inline=True,
            )

            if settings:
                notif_status = []
                if settings.dm_match_reminders:
                    notif_status.append("Match Reminders")
                if settings.dm_trade_notifications:
                    notif_status.append("Trades")
                if settings.dm_waiver_notifications:
                    notif_status.append("Waivers")
                if settings.dm_draft_notifications:
                    notif_status.append("Draft")

                embed.add_field(
                    name="DM Notifications",
                    value=", ".join(notif_status) if notif_status else "All disabled",
                    inline=False,
                )
            else:
                embed.add_field(
                    name="DM Notifications",
                    value="Default settings (all enabled)",
                    inline=False,
                )

            if user.avatar_url:
                embed.set_thumbnail(url=user.avatar_url)

            await interaction.response.send_message(embed=embed, ephemeral=True)

    @account_group.command(name="settings", description="Configure notification settings")
    async def settings(self, interaction: discord.Interaction):
        """Show notification settings configuration."""
        async with get_db_session() as db:
            user_service = UserService(db)
            user = await user_service.get_user_by_discord_id(str(interaction.user.id))

            if not user:
                await interaction.response.send_message(
                    embed=self.error_embed(
                        "Account Not Linked",
                        "Your Discord account isn't linked to PokeDraft yet.\n"
                        "Use `/account link` to get started.",
                    ),
                    ephemeral=True,
                )
                return

            settings = await user_service.get_or_create_notification_settings(
                str(user.id)
            )

            view = NotificationSettingsView(user.id, settings)
            embed = view.get_embed()

            await interaction.response.send_message(
                embed=embed,
                view=view,
                ephemeral=True,
            )

    @account_group.command(name="unlink", description="Unlink your Discord account")
    async def unlink(self, interaction: discord.Interaction):
        """Unlink Discord account from PokeDraft."""
        async with get_db_session() as db:
            user_service = UserService(db)
            user = await user_service.get_user_by_discord_id(str(interaction.user.id))

            if not user:
                await interaction.response.send_message(
                    embed=self.error_embed(
                        "Account Not Linked",
                        "Your Discord account isn't linked to PokeDraft.",
                    ),
                    ephemeral=True,
                )
                return

            # Show confirmation
            view = UnlinkConfirmView(user.id)
            embed = discord.Embed(
                title="Unlink Account?",
                description=(
                    f"Are you sure you want to unlink your Discord from **{user.display_name}**?\n\n"
                    "You will no longer receive Discord notifications and won't be able to "
                    "use Discord commands until you link again."
                ),
                color=Colors.WARNING,
            )

            await interaction.response.send_message(
                embed=embed,
                view=view,
                ephemeral=True,
            )


class NotificationSettingsView(discord.ui.View):
    """View for managing notification settings."""

    def __init__(self, user_id, settings):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.settings = settings

    def get_embed(self) -> discord.Embed:
        """Get the settings embed."""
        embed = discord.Embed(
            title="Notification Settings",
            description="Configure which notifications you receive via DM.",
            color=Colors.INFO,
        )

        def status(enabled: bool) -> str:
            return "Enabled" if enabled else "Disabled"

        embed.add_field(
            name="Match Reminders",
            value=f"{status(self.settings.dm_match_reminders)}\n"
            f"Remind {self.settings.match_reminder_hours_before}h before",
            inline=True,
        )
        embed.add_field(
            name="Trade Notifications",
            value=status(self.settings.dm_trade_notifications),
            inline=True,
        )
        embed.add_field(
            name="Waiver Notifications",
            value=status(self.settings.dm_waiver_notifications),
            inline=True,
        )
        embed.add_field(
            name="Draft Notifications",
            value=status(self.settings.dm_draft_notifications),
            inline=True,
        )
        embed.add_field(
            name="Trade Confirmation",
            value="Required" if self.settings.require_confirmation_for_trades else "Skip",
            inline=True,
        )
        embed.add_field(
            name="Waiver Confirmation",
            value="Required" if self.settings.require_confirmation_for_waivers else "Skip",
            inline=True,
        )

        embed.set_footer(text="Use the buttons below to toggle settings")

        return embed

    @discord.ui.button(label="Match Reminders", style=discord.ButtonStyle.secondary)
    async def toggle_match_reminders(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Toggle match reminders."""
        await self._toggle_setting(interaction, "dm_match_reminders")

    @discord.ui.button(label="Trades", style=discord.ButtonStyle.secondary)
    async def toggle_trades(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Toggle trade notifications."""
        await self._toggle_setting(interaction, "dm_trade_notifications")

    @discord.ui.button(label="Waivers", style=discord.ButtonStyle.secondary)
    async def toggle_waivers(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Toggle waiver notifications."""
        await self._toggle_setting(interaction, "dm_waiver_notifications")

    @discord.ui.button(label="Draft", style=discord.ButtonStyle.secondary)
    async def toggle_draft(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Toggle draft notifications."""
        await self._toggle_setting(interaction, "dm_draft_notifications")

    async def _toggle_setting(
        self, interaction: discord.Interaction, setting_name: str
    ):
        """Toggle a boolean setting."""
        async with get_db_session() as db:
            user_service = UserService(db)
            current_value = getattr(self.settings, setting_name)
            new_value = not current_value

            self.settings = await user_service.update_notification_settings(
                str(self.user_id),
                **{setting_name: new_value},
            )

            await interaction.response.edit_message(embed=self.get_embed(), view=self)


class UnlinkConfirmView(discord.ui.View):
    """Confirmation view for unlinking account."""

    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id

    @discord.ui.button(label="Unlink Account", style=discord.ButtonStyle.danger)
    async def confirm_unlink(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Confirm unlinking."""
        async with get_db_session() as db:
            user_service = UserService(db)
            await user_service.unlink_discord_account(str(self.user_id))

            embed = discord.Embed(
                title="Account Unlinked",
                description="Your Discord account has been unlinked from PokeDraft.\n"
                "Use `/account link` to reconnect anytime.",
                color=Colors.SUCCESS,
            )

            await interaction.response.edit_message(embed=embed, view=None)
            self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Cancel unlinking."""
        embed = discord.Embed(
            title="Cancelled",
            description="Your account remains linked.",
            color=Colors.INFO,
        )

        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()


async def setup(bot: commands.Bot):
    """Set up the account commands cog."""
    await bot.add_cog(AccountCommands(bot))
