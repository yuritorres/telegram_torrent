#
# This is a Telegram bot that integrates with Jackett to allow searching for releases.
#
# --- Prerequisites ---
# 1. Python 3.8+
# 2. `jackett_client.py` (the Jackett interaction module) must be in the same directory.
# 3. A `.env` file in the same directory with the following variables:
#    TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
#    AUTHORIZED_USERS=USERID1,USERID2  (Comma-separated Telegram User IDs)
#    JACKETT_URL=YOUR_JACKETT_INSTANCE_URL (e.g., http://localhost:9117)
#    JACKETT_API_KEY=YOUR_JACKETT_API_KEY
#    (Refer to .env.example for a full template if one was provided)
#
# --- To Run ---
# 1. Install dependencies: pip install -r requirements.txt
#    (Ensure requirements.txt includes python-telegram-bot, python-dotenv, requests)
# 2. Create and configure your .env file based on your settings.
# 3. Run the bot: python telegram_bot.py
#

import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Assuming jackett_client.py is in the same directory
from jackett_client import JackettClient, JackettError
from functools import wraps

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# Authorized users (comma-separated string)
AUTHORIZED_USERS_STR = os.getenv("AUTHORIZED_USERS", "")
AUTHORIZED_USERS = [int(user_id.strip()) for user_id in AUTHORIZED_USERS_STR.split(',') if user_id.strip()]

# Jackett Configuration
JACKETT_URL = os.getenv("JACKETT_URL")
JACKETT_API_KEY = os.getenv("JACKETT_API_KEY")

# Basic logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global JackettClient instance
jackett_client_instance = None

# --- Authorization Decorator ---
def authorized_user_only(func):
    """
    Decorator to restrict access to command handlers to authorized users only.
    Checks if the effective user's ID is in the AUTHORIZED_USERS list.
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not update.effective_user: # Should not happen with command handlers
            logger.error("No effective user found in update, cannot authorize.")
            return

        user_id = update.effective_user.id
        if user_id not in AUTHORIZED_USERS:
            command_name = func.__name__ # Get the name of the command being called
            logger.warning(
                f"Unauthorized access attempt by user ID {user_id} ({update.effective_user.username or 'N/A'}) "
                f"for command /{command_name}."
            )
            await update.message.reply_text(
                "Sorry, you are not authorized to use this command."
            )
            return  # Stop further processing
        
        # User is authorized, proceed with the original command function
        return await func(update, context, *args, **kwargs)
    return wrapper


# --- Command Handlers ---
@authorized_user_only
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued."""
    if not update.message: # Should not happen with CommandHandler
        return
    await update.message.reply_text(
        "Hello! I'm your friendly bot. Use /help to see available commands."
    )

@authorized_user_only
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a help message listing available commands when /help is issued."""
    if not update.message: # Should not happen with CommandHandler
        return
    help_text = (
        "Available commands:\n"
        "/search <query> - Search for releases on Jackett.\n"
        "/help - Show this help message."
    )
    await update.message.reply_text(help_text)

@authorized_user_only
async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /search command to query Jackett."""
    if not update.effective_user or not update.message: # Should be caught by decorator or handler type
        return

    if not context.args:
        await update.message.reply_text(
            "Please provide a search query. Usage: /search <your query>"
        )
        return

    query = " ".join(context.args)
    user_id = update.effective_user.id
    logger.info(f"User {user_id} searching for: '{query}'")

    if not jackett_client_instance:
        logger.warning(f"Jackett client not available for search by user {user_id} for query '{query}'.")
        await update.message.reply_text(
            "Jackett client is not configured or failed to initialize. Please check bot logs."
        )
        return

    try:
        # For now, searching all indexers, no specific categories
        results = await asyncio.to_thread(jackett_client_instance.search, query=query)
        # Note: jackett_client.search is synchronous, so run in thread if it might block.
        # If JackettClient.search becomes async, `await` it directly.

    except JackettConnectionError as e:
        logger.error(f"Jackett connection error for query '{query}' by user {user_id}: {e}")
        await update.message.reply_text("Error connecting to Jackett. Please try again later or contact an admin.")
        return
    except JackettAPIError as e:
        logger.error(f"Jackett API error for query '{query}' by user {user_id}: {e}")
        await update.message.reply_text("Jackett API returned an error. This might be a configuration issue.")
        return
    except JackettParseError as e:
        logger.error(f"Jackett parse error for query '{query}' by user {user_id}: {e}")
        await update.message.reply_text("Failed to parse results from Jackett. The response might be malformed.")
        return
    except JackettSearchError as e: # Raised if all indexers fail
        logger.warning(f"Jackett search failure for query '{query}' by user {user_id}: {e}")
        await update.message.reply_text(f"Search failed for '{query}'. No indexers returned results or all failed.")
        return
    except JackettError as e: # Catch base JackettError for any other specific Jackett issues
        logger.error(f"Generic Jackett error for query '{query}' by user {user_id}: {e}")
        await update.message.reply_text("An error occurred with the Jackett client.")
        return
    except Exception as e:
        logger.error(f"Unexpected error during Jackett search for query '{query}' by user {user_id}: {e}", exc_info=True)
        await update.message.reply_text("An unexpected error occurred while searching. Please try again later.")
        return

    if not results:
        await update.message.reply_text(f"No results found for your query: '{query}'")
        return

    # Send results, one message per result to avoid hitting message length limits
    # And to allow users to interact with individual links easily.
    num_results_to_send = min(len(results), 10) # Limit to sending max 10 results to avoid spam
    
    await update.message.reply_text(f"Found {len(results)} results for '{query}'. Displaying top {num_results_to_send}:")

    for i, result in enumerate(results[:num_results_to_send]):
        size_bytes = result.get('size', 0)
        size_human = "N/A"
        if isinstance(size_bytes, int) and size_bytes > 0:
            if size_bytes >= 1024**3: # GB
                size_human = f"{size_bytes / (1024**3):.2f} GB"
            elif size_bytes >= 1024**2: # MB
                size_human = f"{size_bytes / (1024**2):.2f} MB"
            elif size_bytes >= 1024: # KB
                size_human = f"{size_bytes / 1024:.2f} KB"
            else: # Bytes
                size_human = f"{size_bytes} B"
        
        formatted_result = (
            f"Title: {result.get('title', 'N/A')}\n"
            f"Size: {size_human}\n"
            f"Seeders: {result.get('seeders', 'N/A')}, Leechers: {result.get('leechers', 'N/A')}\n"
            f"Link: {result.get('link', 'N/A')}\n"
            f"Indexer: {result.get('indexer', 'N/A')}\n"
            f"Published: {result.get('pub_date', 'N/A')}"
        )
        try:
            await update.message.reply_text(formatted_result, disable_web_page_preview=True)
        except Exception as e: # Handle potential errors sending individual messages
            logger.error(f"Error sending result message for query '{query}' by user {user_id}: {e}. Result: {result.get('title')}")
            await update.message.reply_text(f"Error sending one of the results ({result.get('title', 'Unknown Title')}). Some results may be missing.")
            # Potentially break or continue based on error type

    if len(results) > num_results_to_send:
        await update.message.reply_text(f"Sent the top {num_results_to_send} of {len(results)} total results.")


# --- Global Error Handler ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log Errors caused by Updates."""
    logger.error("Exception while handling an update/event:", exc_info=context.error)

    # More detailed logging if update object is available
    if update:
        update_details = "N/A"
        if isinstance(update, Update):
            if update.effective_user:
                update_details = f"User: {update.effective_user.id} ({update.effective_user.username or 'N/A'})"
            if update.effective_chat:
                update_details += f", Chat: {update.effective_chat.id} ({update.effective_chat.title or update.effective_chat.type})"
            if update.update_id:
                 update_details += f", Update ID: {update.update_id}"
        else: # update might be something else like a job in a JobQueue
            update_details = str(update)
        
        logger.error(f"Update details: {update_details}\nCaused error: {context.error}")
    else:
        logger.error(f"Application error (no update object available): {context.error}")

    # Optionally, try to inform the user if it's an Update-related error
    if isinstance(update, Update) and update.effective_chat:
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Sorry, an unexpected error occurred. The developers have been notified."
            )
        except Exception as e:
            logger.error(f"Failed to send error message to user {update.effective_chat.id}: {e}")


async def main() -> None:
    """Starts the Telegram bot."""
    global jackett_client_instance

    # --- Configuration Validation ---
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in .env file. Bot cannot start.")
        return
    if not AUTHORIZED_USERS:
        logger.warning("AUTHORIZED_USERS not set or empty in .env file. No users will be able to use commands.")
    if not JACKETT_URL or not JACKETT_API_KEY:
        logger.error("JACKETT_URL or JACKETT_API_KEY not found in .env file. Jackett functionality will be disabled.")
        # Depending on desired behavior, you might allow the bot to start without Jackett
        # For now, let's initialize it but it will fail if used.
        # Or, decide not to initialize:
        # return
    
    try:
        if JACKETT_URL and JACKETT_API_KEY:
            jackett_client_instance = JackettClient(jackett_url=JACKETT_URL, api_key=JACKETT_API_KEY)
            logger.info("JackettClient initialized successfully.")
        else:
            logger.warning("JackettClient not initialized due to missing URL or API Key.")
            # jackett_client_instance will remain None
            
    except ValueError as e: # Catch specific error from JackettClient.__init__
        logger.error(f"Error initializing JackettClient: {e}. Jackett functionality will be disabled.")
        # jackett_client_instance will remain None
    except Exception as e: # Catch any other unexpected error during Jackett init
        logger.error(f"Unexpected error initializing JackettClient: {e}. Jackett functionality will be disabled.")
        # jackett_client_instance will remain None


    # --- Application Setup ---
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # --- Add command handlers ---
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("search", search_command))

    # --- Register Global Error Handler ---
    # This should typically be one of the last handlers added.
    application.add_error_handler(error_handler)
    
    logger.info("Telegram bot starting...")
    await application.run_polling()

if __name__ == "__main__":
    # Ensure the event loop is managed correctly if not using `run_polling`'s default.
    # For `run_polling`, this is generally handled.
    # If you were to use `start_polling` and `idle` or other async setups,
    # you might need `asyncio.get_event_loop().run_until_complete(main())` or similar.
    # For now, `asyncio.run(main())` is suitable if Python version allows (3.7+) for top-level await,
    # but `python-telegram-bot` often handles its own loop with `run_polling`.
    # Let's stick to a simple direct call for now if `run_polling` is used.
    # However, `run_polling` itself is async, so `main` needs to be run in an event loop.
    # A simple way for scripts:
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user.")
    except Exception as e:
        logger.error(f"Unhandled exception in main: {e}", exc_info=True)
