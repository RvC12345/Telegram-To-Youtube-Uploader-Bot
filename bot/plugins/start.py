from pyrogram import filters as Filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from ..translations import Messages as tr
from ..config import Config
from ..utubebot import UtubeBot
import shutil

@UtubeBot.on_message(
    Filters.private
    & Filters.incoming
    & Filters.command("start")
    & Filters.user(Config.AUTH_USERS)
)
async def _start(c: UtubeBot, m: Message):
    #await m.reply_chat_action("typing")
    await m.reply_text(
        text=tr.START_MSG.format(m.from_user.first_name),
        quote=True,
        disable_web_page_preview=True,
            )



def human_readable_size(size_in_bytes):
    """Convert bytes to a human-readable format (KB, MB, GB, etc.)."""
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024


@UtubeBot.on_message(Filters.command("disc") & Filters.private)
async def disc_usage(client, message):
    # Get disk usage
    total, used, free = shutil.disk_usage("/")
    
    # Convert to human-readable format
    total_hr = human_readable_size(total)
    used_hr = human_readable_size(used)
    free_hr = human_readable_size(free)
    
    # Create the response message
    response = (
        f"💾 **Disk Usage**:\n"
        f"• Total: {total_hr}\n"
        f"• Used: {used_hr}\n"
        f"• Free: {free_hr}"
    )
    
    # Send the response to the user
    await message.reply_text(response)

