import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

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


async def send_timetable(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now().strftime("%A")
    logging.info(f"Sending timetable for {today}")

    if today in timetable:
        for period in timetable[today]:
            if "msg" in period:
                await update.message.reply_text(period["msg"])
                return

        message = f"<b>Here's your timetable for today, {today}! 🙃</b>\n"
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
                    # f"• <b>Duration :</b> {period['duration']} minutes\n"
                    f"• <b>Faculty :</b> {period.get('teacher', 'N/A')}\n"
                    f"• <b>Room :</b> {period.get('room', 'N/A')}\n\n"
                )

        message += f"<code>----------------------------</code>\n"
        message += "<b>That's your schedule! 😎 Have a great day! ✨</b>"

        await update.message.reply_text(message, parse_mode="HTML")
    else:
        await update.message.reply_text(f"No timetable available for {today}.")


async def send_break_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now().strftime("%A")
    logging.info(f"Checking break status for {today}")

    if today in timetable:
        for period in timetable[today]:
            if "msg" in period:
                await update.message.reply_text(period["msg"])
                return

    if today not in timetable:
        await update.message.reply_text(f"No timetable available for {today}.")
        return

    current_time = datetime.now().time()
    ongoing_break = False

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

    if not ongoing_break:
        await update.message.reply_text("No breaks currently. Stay focused!")


async def send_current_period(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now().strftime("%A")
    logging.info(f"Checking current period for {today}")

    if today not in timetable:
        await update.message.reply_text(f"No timetable available for {today}.")
        return

    for period in timetable[today]:
        if "msg" in period:
            await update.message.reply_text(period["msg"])
            return

    current_time = datetime.now()
    cutoff_start_time = datetime.strptime("09:30", "%H:%M").time()
    cutoff_end_time = datetime.strptime("16:30", "%H:%M").time()

    if current_time.time() < cutoff_start_time:
        await update.message.reply_text("Let the class start! 📚")
        return

    if current_time.time() >= cutoff_end_time:
        await update.message.reply_text("Classes are over! Enjoy your evening! 🌆")
        return

    for period in timetable[today]:
        period_start = datetime.strptime(period["time"], "%H:%M").replace(
            year=current_time.year, month=current_time.month, day=current_time.day
        )
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
                    f"• <b>Duration :</b> {period['duration']} minutes\n"
                    f"• <b>Faculty :</b> {period.get('teacher', 'N/A')}\n"
                    f"• <b>Room :</b> {period.get('room', 'N/A')}\n"
                )
                await update.message.reply_text(reminder_message, parse_mode="HTML")
            return

    await update.message.reply_text("No period is currently scheduled.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Yo CSBS '27! 👋 All set? I’ve got your classes, rooms, and breaks under control. No skipping, no excuses. Let’s get this over with! 😎\n\n"
        f"Available commands:\n"
        f"/timetable - View today's timetable\n"
        f"/breaktime - Check current break status\n"
        f"/whatsnow - View current period"
    )


def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("No TELEGRAM_TOKEN found in environment variables")

    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("timetable", send_timetable))
    application.add_handler(CommandHandler("breaktime", send_break_message))
    application.add_handler(CommandHandler("whatsnow", send_current_period))

    application.run_polling(port=8080)


if __name__ == "__main__":
    main()
