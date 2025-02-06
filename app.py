# Import necessary libraries
from flask import Flask
import logging
import os
import json
from datetime import datetime, timedelta, time
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, JobQueue
from pymongo import MongoClient
import pytz
import asyncio
from telegram.error import TimedOut, NetworkError, RetryAfter

# Initialize timezone for India
india_tz = pytz.timezone("Asia/Kolkata")

# Load environment variables and timetable
load_dotenv()

with open('timetable.json', 'r') as f:
    timetable = json.load(f)

# Initialize MongoDB connection
mongo_client = MongoClient(os.getenv("MONGODB_URI"))
db = mongo_client["telebot_db"]
users_collection = db["users"]

# Setup logging and Flask app
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

app = Flask(__name__)

# some constants
MAX_RETRIES = 3
RETRY_DELAY = 300
DAILY_TIMETABLE_HOUR = 8
DAILY_TIMETABLE_MINUTE = 31
CONNECTION_RETRIES = 5
CONNECTION_RETRY_DELAY = 5
CONNECTION_TIMEOUT = 30

# Health check endpoint
@app.route("/health", methods=["GET"])
def health_check():
    return "Server is alive!", 200


# Database operations
def add_user_info(user):
    """Add or update user information in MongoDB."""
    user_data = {
        "user_id": user.id,
        "first_name": user.first_name,
    }

    if not users_collection.find_one({"user_id": user.id}):
        users_collection.insert_one(user_data)


async def get_chat_ids():
    """Retrieve all user chat IDs from database."""
    chat_ids = []
    users = users_collection.find({}, {"user_id": 1})
    for user in users:
        chat_ids.append(user["user_id"])
    return chat_ids


# Timetable distribution functions
async def send_timetable_to_all_users(context: ContextTypes.DEFAULT_TYPE):
    """Send daily timetable to all registered users at scheduled time."""
    chat_ids = await get_chat_ids()
    today = datetime.now(india_tz).strftime("%A")
    logging.info(f"Sending timetable for {today} to all users")

    for period in timetable[today]:
        if "msg" in period:
            logging.info(f"{period['msg']}")
            return

    message = f"<b>It’s {today}. Here’s your damn timetable. Don’t be late!</b>\n"
    message += f"<code>----------------------------</code>\n\n"

    for period in timetable[today]:
        start_time = datetime.strptime(period["time"], "%H:%M")
        end_time = start_time + timedelta(minutes=period["duration"])

        formatted_start_time = start_time.strftime("%I:%M %p")
        formatted_end_time = end_time.strftime("%I:%M %p")

        if period["subject"] == "Break":
            message += (
                f"<i>&lt;-- BREAK 😀 : {period['duration']} Minutes --&gt;</i>\n\n"
            )
        else:
            message += (
                f"• <b>Subject :</b> {period['subject']}\n"
                f"• <b>Time :</b> {formatted_start_time} to {formatted_end_time}\n"
                f"• <b>Faculty :</b> {period.get('teacher', 'N/A')}\n"
                f"• <b>Room :</b> {period.get('room', 'N/A')}\n\n"
            )

    message += f"<code>----------------------------</code>\n"
    message += "<b>That’s it. Now go, and don’t screw it up!</b>"

    for chat_id in chat_ids:
        await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")


async def send_timetable(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command handler to send timetable on user request."""
    await get_chat_ids()
    today = datetime.now(india_tz).strftime("%A")
    logging.info(f"Sending timetable for {today}")

    if today not in timetable:
        await update.message.reply_text(f"No timetable available for {today}.")
        return

    if today in timetable:
        for period in timetable[today]:
            if "msg" in period:
                await update.message.reply_text(period["msg"])
                return

        message = f"<b>It’s {today}. Here’s your damn timetable. Don’t be late!</b>\n"
        message += f"<code>----------------------------</code>\n\n"

        for period in timetable[today]:
            start_time = datetime.strptime(period["time"], "%H:%M")
            end_time = start_time + timedelta(minutes=period["duration"])

            formatted_start_time = start_time.strftime("%I:%M %p")
            formatted_end_time = end_time.strftime("%I:%M %p")

            if period["subject"] == "Break":
                message += (
                    f"<i>&lt;-- BREAK 😀 : {period['duration']} Minutes --&gt;</i>\n\n"
                )
            else:
                message += (
                    f"• <b>Subject :</b> {period['subject']}\n"
                    f"• <b>Time :</b> {formatted_start_time} to {formatted_end_time}\n"
                    f"• <b>Faculty :</b> {period.get('teacher', 'N/A')}\n"
                    f"• <b>Room :</b> {period.get('room', 'N/A')}\n\n"
                )

        message += f"<code>----------------------------</code>\n"
        message += "<b>That’s it. Now go, and don’t screw it up!</b>"

        await update.message.reply_text(message, parse_mode="HTML")
    else:
        await update.message.reply_text(f"No timetable available for {today}.")


# Break time management
async def send_break_message_force(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command handler to check current/next break status."""
    today = datetime.now(india_tz).strftime("%A")
    logging.info(f"Checking break status for {today}")

    if today not in timetable:
        await update.message.reply_text(f"No timetable available for {today}.")
        return

    for period in timetable[today]:
        if "msg" in period:
            await update.message.reply_text(period["msg"])
            return

    current_time = datetime.now(india_tz).time()
    ongoing_break = False
    next_break_time = None

    cutoff_start_time = datetime.strptime("09:30", "%H:%M").time()
    cutoff_end_time = datetime.strptime("16:30", "%H:%M").time()

    if current_time < cutoff_start_time:
        await update.message.reply_text("Hold up! Class hasn't started yet! 📚")
        return

    if current_time >= cutoff_end_time:
        await update.message.reply_text(
            "Classes are over, now get lost! See you tomorrow!"
        )
        return

    for period in timetable[today]:
        if period["subject"] == "Break":
            break_time = datetime.strptime(period["time"], "%H:%M").time()
            break_end_time = (
                datetime.combine(datetime.today(), break_time)
                + timedelta(minutes=period["duration"])
            ).time()

            if break_time <= current_time < break_end_time:
                ongoing_break = True
                await update.message.reply_text(
                    f"<b>Break Time!</b> 😋\n<code>---------------</code>\nYou have a {period['duration']} minute break.",
                    parse_mode="HTML",
                )
                return

            if not ongoing_break and current_time < break_time:
                next_break_time = break_time
                break_duration = period["duration"]
                break

    if not ongoing_break:
        if next_break_time:
            formatted_next_break_time = break_time.strftime("%I:%M %p")
            await update.message.reply_text(
                f"No breaks currently. Your next break is at {formatted_next_break_time} for {break_duration} minutes. Stay focused!"
            )
        else:
            await update.message.reply_text("No breaks currently. Stay focused!")


break_message_sent = {}


async def schedule_break_notifications(context: ContextTypes.DEFAULT_TYPE):
    """Automated function to send break notifications."""
    today = datetime.now(india_tz).strftime("%A")
    current_time = datetime.now(india_tz)

    if today not in timetable:
        return  # No timetable available for today

    for period in timetable[today]:
        if period["subject"] == "Break":
            break_start = datetime.strptime(period["time"], "%H:%M").replace(
                year=current_time.year, month=current_time.month, day=current_time.day
            )
            break_start = india_tz.localize(break_start)
            break_end = break_start + timedelta(minutes=period["duration"])

            notification_time = break_start - timedelta(minutes=1)

            if current_time >= notification_time and current_time < break_start:
                message = (
                    f"<b>Break Time!</b> 😋\n<code>---------------</code>\nYou have a {period['duration']} minute break."
                )
                chat_ids = await get_chat_ids()
                for chat_id in chat_ids:
                    await context.bot.send_message(
                        chat_id=chat_id, text=message, parse_mode="HTML"
                    )
                break


# Period management and notifications
async def schedule_next_period_notifications(context: ContextTypes.DEFAULT_TYPE):
    """Send notifications 5 minutes before next period."""
    today = datetime.now(india_tz).strftime("%A")
    current_time = datetime.now(india_tz)

    logging.info(f"Checking for next period notifications at {current_time}")

    if today not in timetable:
        logging.info(f"No timetable available for {today}")
        return

    next_period = None
    for period in timetable[today]:
        if period["subject"] == "Break":
            continue

        period_start = datetime.strptime(period["time"], "%H:%M").replace(
            year=current_time.year, month=current_time.month, day=current_time.day
        )
        period_start = india_tz.localize(period_start)

        if period_start > current_time:
            next_period = period
            break

    if next_period:
        notification_time = period_start - timedelta(minutes=5)

        logging.info(f"Next period: {next_period['subject']} at {period_start}")
        logging.info(f"Notification time: {notification_time}")
        logging.info(f"Current time: {current_time}")

        if current_time >= notification_time and current_time < period_start:
            message = (
                f"<b>Next Period (Starts in 5min):</b>\n"
                f"<code>---------------</code>\n"
                f"• <b>Subject :</b> {next_period['subject']}\n"
                f"• <b>Time :</b> {period_start.strftime('%I:%M %p')} to {(period_start + timedelta(minutes=next_period['duration'])).strftime('%I:%M %p')}\n"
                f"• <b>Faculty :</b> {next_period.get('teacher', 'N/A')}\n"
                f"• <b>Room :</b> {next_period.get('room', 'N/A')}\n"
            )
            chat_ids = await get_chat_ids()
            for chat_id in chat_ids:
                try:
                    await context.bot.send_message(
                        chat_id=chat_id, text=message, parse_mode="HTML"
                    )
                    logging.info(f"Sent next period notification to chat_id: {chat_id}")
                except Exception as e:
                    logging.error(
                        f"Failed to send message to chat_id {chat_id}: {str(e)}"
                    )
        else:
            logging.info("Not within the notification window for the next period")
    else:
        logging.info("No upcoming periods found")


async def send_current_period(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command handler to show current ongoing period."""
    today = datetime.now(india_tz).strftime("%A")
    logging.info(f"Checking current period for {today}")

    if today not in timetable:
        await update.message.reply_text(f"No timetable available for {today}.")
        return

    for period in timetable[today]:
        if "msg" in period:
            await update.message.reply_text(period["msg"])
            return

    current_time = datetime.now(india_tz)
    cutoff_start_time = datetime.strptime("09:30", "%H:%M").time()
    cutoff_end_time = datetime.strptime("16:30", "%H:%M").time()

    if current_time.time() < cutoff_start_time:
        await update.message.reply_text("Hold up! Class hasn't started yet! 📚")
        return

    if current_time.time() >= cutoff_end_time:
        await update.message.reply_text(
            "Classes are over, now get lost! See you tomorrow!"
        )
        return

    for period in timetable[today]:
        period_start = datetime.strptime(period["time"], "%H:%M").replace(
            year=current_time.year, month=current_time.month, day=current_time.day
        )

        period_start = india_tz.localize(period_start)
        period_end = period_start + timedelta(minutes=period["duration"])

        if period_start <= current_time < period_end:
            if period["subject"] == "Break":
                await update.message.reply_text(
                    f"<b>Break Time!</b> 😋\n<code>---------------</code>\nYou have a {period['duration']} minute break.",
                    parse_mode="HTML",
                )
            else:
                reminder_message = (
                    f"<b>Current Period:</b>\n"
                    f"<code>---------------</code>\n"
                    f"• <b>Subject :</b> {period['subject']}\n"
                    f"• <b>Time :</b> {period_start.strftime('%I:%M %p')} to {period_end.strftime('%I:%M %p')}\n"
                )
                reminder_message += (
                    f"• <b>Faculty :</b> {period.get('teacher', 'N/A')}\n"
                    f"• <b>Room :</b> {period.get('room', 'N/A')}\n"
                )
                await update.message.reply_text(reminder_message, parse_mode="HTML")
            return

    await update.message.reply_text("No period is currently scheduled.")


# User interaction commands
async def send_support_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send GitHub repository link and support message."""
    support_message = (
        "If you enjoy using this bot, please consider starring our GitHub repository! 🌟\n\n"
        "https://github.com/ABHAY-100/zephyr-telegram-bot"
    )
    await update.message.reply_text(support_message, parse_mode="HTML")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initialize bot for new users and show available commands."""
    user = update.message.from_user
    add_user_info(user)

    await update.message.reply_text(
        f"<b>Hey CSBS '27,</b> you lost souls! Your personal schedule demon here. Ready to make your life slightly less chaotic?\n\n"
        f"Commands to keep your clueless self on track:\n"
        f"/timetable - Your daily doom schedule\n"
        f"/breaktime - Freedom time or nah?\n"
        f"/whatsnow - Where your lazy self should be\n"
        f"/supportus - Like my chaos? Star us on GitHub!\n\n"
        f"Now try a command, if you can handle it. 🤠",
        parse_mode="HTML",
    )

# Add new utility function for scheduling
async def schedule_with_retry(func, context: ContextTypes.DEFAULT_TYPE, retry_count=0):
    """Utility function to retry failed scheduled tasks."""
    try:
        await func(context)
        logging.info(f"Successfully executed {func.__name__}")
    except Exception as e:
        logging.error(f"Error in {func.__name__}: {str(e)}")
        if retry_count < MAX_RETRIES:
            logging.info(f"Retrying {func.__name__} in {RETRY_DELAY} seconds...")
            await asyncio.sleep(RETRY_DELAY)
            await schedule_with_retry(func, context, retry_count + 1)
        else:
            logging.error(f"Max retries reached for {func.__name__}")

# Add retry decorator for network operations
def handle_telegram_errors(func):
    async def wrapper(*args, **kwargs):
        for attempt in range(CONNECTION_RETRIES):
            try:
                return await func(*args, **kwargs)
            except (TimedOut, NetworkError) as e:
                if attempt == CONNECTION_RETRIES - 1:
                    logging.error(f"Max retries reached for {func.__name__}: {str(e)}")
                    raise
                logging.warning(f"Connection error in {func.__name__}, retrying... ({attempt + 1}/{CONNECTION_RETRIES})")
                await asyncio.sleep(CONNECTION_RETRY_DELAY)
            except RetryAfter as e:
                logging.warning(f"Rate limited, waiting {e.retry_after} seconds")
                await asyncio.sleep(e.retry_after)
                return await func(*args, **kwargs)
    return wrapper

# Main application setup
def main():
    """Initialize and configure the bot with all handlers and scheduled jobs."""
    token = os.getenv("TELEGRAM_TOKEN")

    if not token:
        raise ValueError("No TELEGRAM_TOKEN found in environment variables")

    # Configure application with proper timeout settings
    application = (
        ApplicationBuilder()
        .token(token)
        .connect_timeout(CONNECTION_TIMEOUT)
        .read_timeout(CONNECTION_TIMEOUT)
        .write_timeout(CONNECTION_TIMEOUT)
        .pool_timeout(CONNECTION_TIMEOUT)
        .build()
    )

    # Add error handler for the application
    async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        logging.error(f"Exception while handling an update: {context.error}")
        if isinstance(context.error, (TimedOut, NetworkError)):
            logging.warning("Network error occurred, will retry on next update")
        elif isinstance(context.error, RetryAfter):
            logging.warning(f"Rate limited, waiting {context.error.retry_after} seconds")
            await asyncio.sleep(context.error.retry_after)

    application.add_error_handler(error_handler)

    # Add command handlers with retry decorator
    application.add_handler(CommandHandler("start", handle_telegram_errors(start)))
    application.add_handler(CommandHandler("timetable", handle_telegram_errors(send_timetable)))
    application.add_handler(CommandHandler("breaktime", handle_telegram_errors(send_break_message_force)))
    application.add_handler(CommandHandler("whatsnow", handle_telegram_errors(send_current_period)))
    application.add_handler(CommandHandler("supportus", handle_telegram_errors(send_support_message)))

    # Schedule daily timetable message with better timing control
    now = datetime.now(india_tz)
    next_run_time = now.replace(
        hour=DAILY_TIMETABLE_HOUR,
        minute=DAILY_TIMETABLE_MINUTE,
        second=0,
        microsecond=0
    )
    
    if now >= next_run_time:
        next_run_time += timedelta(days=1)
    
    delay_seconds = (next_run_time - now).total_seconds()
    
    # Schedule daily timetable with retry mechanism
    application.job_queue.run_once(
        lambda ctx: schedule_with_retry(send_timetable_to_all_users, ctx),
        delay_seconds,
        name="daily_timetable"
    )

    # Schedule break notifications with better interval control
    application.job_queue.run_repeating(
        lambda ctx: schedule_with_retry(schedule_break_notifications, ctx),
        interval=60,
        first=5,  # Start after 5 seconds
        name="break_notifications"
    )

    # Schedule next period notifications with optimized interval
    application.job_queue.run_repeating(
        lambda ctx: schedule_with_retry(schedule_next_period_notifications, ctx),
        interval=180,
        first=10,  # Start after 10 seconds to prevent overlap
        name="period_notifications"
    )

    # Add job status monitoring - Fixed version
    async def monitor_jobs(context: ContextTypes.DEFAULT_TYPE):
        """Monitor scheduled jobs and log their status."""
        jobs = context.job_queue.jobs()
        for job in jobs:
            logging.info(f"Job {job.name}: Next run at {job.next_t}")

    application.job_queue.run_repeating(
        monitor_jobs,
        interval=300,  # Every 5 minutes
        first=15,  # Start after 15 seconds
        name="job_monitor"
    )

    # Replace gunicorn with waitress for Windows compatibility
    from threading import Thread
    from waitress import serve

    def run_flask():
        serve(app, host='0.0.0.0', port=8080)

    Thread(target=run_flask).start()

    # Start the bot with error handling
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        raise


if __name__ == "__main__":
    main()

