from flask import Flask
import logging
import os
from datetime import datetime, timedelta, time
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, JobQueue
from pymongo import MongoClient
import pytz

india_tz = pytz.timezone("Asia/Kolkata")

load_dotenv()

mongo_client = MongoClient(os.getenv("MONGODB_URI"))
db = mongo_client["test-database"]
users_collection = db["test-users"]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

app = Flask(__name__)

timetable = {
    "Saturday": [
        {
            "msg": "No classes on Saturday",
        }
    ],
    "Sunday": [
        {
            "msg": "No classes on Sunday",
        }
    ],
    "Monday": [
        {  # 1st & 2nd Hour
            "subject": "DBMS",
            "time": "09:30",
            "room": "301",
            "teacher": "Chitra Miss",
            "duration": 115,
        },
        {  # Break
            "subject": "Break",
            "time": "11:25",
            "duration": 10,
        },
        {  # 3rd Hour
            "subject": "COA",
            "time": "11:35",
            "room": "301",
            "teacher": "Amrita Miss",
            "duration": 55,
        },
        {  # Break
            "subject": "Break",
            "time": "12:30",
            "duration": 60,
        },
        {  # 4th Hour
            "subject": "COI",
            "time": "13:30",
            "room": "211",
            "teacher": "Manju K",
            "duration": 60,
        },
        {  # HNRS/MNRS
            "subject": "HNRS/MNRS",
            "time": "14:30",
            "room": "N/A",
            "duration": 120,
        },
    ],
    "Tuesday": [
        {  # 1st Hour
            "subject": "OS",
            "time": "09:30",
            "room": "B303",
            "teacher": "Maria Miss",
            "duration": 60,
        },
        {  # 2nd Hour
            "subject": "COA",
            "time": "10:30",
            "room": "B303",
            "teacher": "Amrita Miss",
            "duration": 55,
        },
        {  # Break
            "subject": "Break",
            "time": "11:25",
            "duration": 10,
        },
        {  # 3rd Hour
            "subject": "OS",
            "time": "11:35",
            "room": "B303",
            "teacher": "Maria Miss",
            "duration": 55,
        },
        {  # Break
            "subject": "Break",
            "time": "12:30",
            "duration": 60,
        },
        {  # LAB
            "subject": "DBMS/STAT LAB",
            "time": "13:30",
            "room": "LAB 1",
            "teacher": "Areelum Okkay Avide Undakum",
            "duration": 180,
        },
    ],
    "Wednesday": [
        {  # 1st & 2nd Hour
            "subject": "MATHS",
            "time": "09:30",
            "room": "B303",
            "teacher": "MKK",
            "duration": 115,
        },
        {  # Break
            "subject": "Break",
            "time": "11:25",
            "duration": 10,
        },
        {  # 3rd Hour
            "subject": "PE",
            "time": "11:35",
            "room": "B303",
            "teacher": "TI",
            "duration": 55,
        },
        {  # Break
            "subject": "Break",
            "time": "12:30",
            "duration": 60,
        },
        {  # 4th Hour
            "subject": "DBMS",
            "time": "13:30",
            "room": "B303",
            "teacher": "Chitra Miss",
            "duration": 60,
        },
        {  # HNRS/MNRS
            "subject": "HNRS/MNRS",
            "time": "14:30",
            "room": "101",
            "duration": 120,
        },
    ],
    "Thursday": [
        {  # 1st Hour
            "subject": "DBMS",
            "time": "09:30",
            "room": "B303",
            "teacher": "Chitra Miss",
            "duration": 60,
        },
        {  # 2nd Hour
            "subject": "COA",
            "time": "10:30",
            "room": "B303",
            "teacher": "Amrita Miss",
            "duration": 55,
        },
        {  # Break
            "subject": "Break",
            "time": "11:25",
            "duration": 10,
        },
        {  # 3rd Hour
            "subject": "C0A",
            "time": "11:35",
            "room": "B303",
            "teacher": "Amrita Miss",
            "duration": 55,
        },
        {  # Break
            "subject": "Break",
            "time": "12:30",
            "duration": 60,
        },
        {  # 4th Hour
            "subject": "OS",
            "time": "13:30",
            "room": "B303",
            "teacher": "Maria Miss",
            "duration": 60,
        },
        {  # 5h Hour
            "subject": "MATHS",
            "time": "14:30",
            "room": "B303",
            "teacher": "MKK",
            "duration": 55,
        },
        {  # Break
            "subject": "Break",
            "time": "15:25",
            "duration": 10,
        },
        {  # 6h Hour
            "subject": "COI",
            "time": "15:35",
            "room": "B303",
            "teacher": "Manju K",
            "duration": 55,
        },
    ],
    "Friday": [
        {  # 1st Hour
            "subject": "OS",
            "time": "09:30",
            "room": "B304",
            "teacher": "Maria Miss",
            "duration": 50,
        },
        {  # 2nd Hour
            "subject": "MATHS",
            "time": "10:20",
            "room": "B304",
            "teacher": "MKK",
            "duration": 50,
        },
        {  # Break
            "subject": "Break",
            "time": "11:10",
            "duration": 10,
        },
        {  # 3rd Hour
            "subject": "PE",
            "time": "11:20",
            "room": "B304",
            "teacher": "TI",
            "duration": 50,
        },
        {  # Break
            "subject": "Break",
            "time": "12:10",
            "duration": 180,
        },
        {  # LAB
            "subject": "DBMS/STAT LAB",
            "time": "14:00",
            "room": "LAB 1",
            "teacher": "Areelum Okkay Avide Undakum",
            "duration": 180,
        },
    ],
}


@app.route("/health", methods=["GET"])
def health_check():
    return "Server is alive!", 200


def add_user_info(user):
    user_data = {
        "user_id": user.id,
        "first_name": user.first_name,
    }

    if not users_collection.find_one({"user_id": user.id}):
        users_collection.insert_one(user_data)


async def get_chat_ids():
    chat_ids = []
    users = users_collection.find({}, {"user_id": 1})
    for user in users:
        chat_ids.append(user["user_id"])
    return chat_ids


async def send_timetable_to_all_users(context: ContextTypes.DEFAULT_TYPE):
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


async def send_break_message_force(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                    # f"<b>Break Time in 1 minute!</b> 😋\n"
                    # f"<code>---------------</code>\n"
                    # f"You have a {period['duration']} minute break starting at {break_start.strftime('%I:%M %p')}."
                    f"<b>Break Time!</b> 😋\n<code>---------------</code>\nYou have a {period['duration']} minute break."
                )
                chat_ids = await get_chat_ids()
                for chat_id in chat_ids:
                    await context.bot.send_message(
                        chat_id=chat_id, text=message, parse_mode="HTML"
                    )
                break


async def schedule_next_period_notifications(context: ContextTypes.DEFAULT_TYPE):
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


async def send_support_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    support_message = (
        "If you enjoy using this bot, please consider starring our GitHub repository! 🌟\n\n"
        "https://github.com/ABHAY-100/zephyr-telegram-bot"
    )
    await update.message.reply_text(support_message, parse_mode="HTML")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


def main():
    token = os.getenv("TELEGRAM_TOKEN")

    if not token:
        raise ValueError("No TELEGRAM_TOKEN found in environment variables")

    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("timetable", send_timetable))
    application.add_handler(CommandHandler("breaktime", send_break_message_force))
    application.add_handler(CommandHandler("whatsnow", send_current_period))
    application.add_handler(CommandHandler("supportus", send_support_message))

    # The 8:30 timetable msg
    now = datetime.now(india_tz)
    next_run_time = now.replace(hour=8, minute=30, second=0, microsecond=0)
    if now >= next_run_time:
        next_run_time += timedelta(days=1)
    delay_seconds = (next_run_time - now).total_seconds()
    application.job_queue.run_once(send_timetable_to_all_users, delay_seconds)

    # Check for break time every minute
    application.job_queue.run_repeating(
        schedule_break_notifications, interval=60, first=0
    )

    # Check for next period every minute
    application.job_queue.run_repeating(
        schedule_next_period_notifications, interval=180, first=0
    )

    from threading import Thread

    def run_flask():
        app.run(host="0.0.0.0", port=8080)

    Thread(target=run_flask).start()

    application.run_polling()


if __name__ == "__main__":
    main()

