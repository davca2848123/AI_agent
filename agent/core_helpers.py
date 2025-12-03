# Helper methods to add to AutonomousAgent class

async def handle_command(self, msg: dict):
    """Handle Discord commands."""
    await self.command_handler.handle_command(msg)
