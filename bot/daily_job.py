import asyncio
import datetime
import os
import random
import time
from zoneinfo import ZoneInfo

import schedule
from dotenv import load_dotenv
from telegram import Bot

from db.db import get_conn
from fill_form_razer_async import fill_and_submit
from submit_photo_async import upload_photo
from .check_email import get_invitation_link

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
MAX_CONCURRENT_USERS = os.environ.get("MAX_CONCURRENT_USERS")
EARLY_PREP_JOB_HOUR = os.environ.get("EARLY_PREP_JOB_HOUR")
EARLY_PREP_JOB_MIN = os.environ.get("EARLY_PREP_JOB_MIN")
START_JOB_HOUR = os.environ.get("START_JOB_HOUR")
START_JOB_MIN = os.environ.get("START_JOB_MIN")
END_JOB_HOUR = os.environ.get("END_JOB_HOUR")
END_JOB_MIN = os.environ.get("END_JOB_MIN")
ALL_DAYS = os.environ.get("ALL_DAYS")
TIMEZONE = os.environ.get("TIMEZONE")

semaphore = asyncio.Semaphore(int(MAX_CONCURRENT_USERS))
SG_TZ = ZoneInfo(TIMEZONE)


async def job():
    print("Job started")

    with get_conn() as conn:
        rows = conn.execute("""
            SELECT u.name, u.email, u.face_photo_path, j.id
            FROM job j
            INNER JOIN user u ON u.id = j.id
            WHERE j.active = 1
        """,
                            ).fetchall()

    tasks = []
    logs = []

    for row in rows:
        if row is None:
            pass
        if not row[0] or not row[1] or not row[2]:
            with get_conn() as conn:
                conn.execute("""
                    INSERT INTO job_run (user_id, status, name, email, face_photo_path, error)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                             (row[3], "Failed", row[0], row[1], row[2], "Unknown"))
        else:
            trigger_ts = random_trigger_timestamp(
                START_JOB_HOUR,
                START_JOB_MIN,
                END_JOB_HOUR,
                END_JOB_MIN
            )
            tasks.append(
                asyncio.create_task(process_user(row, trigger_ts))
            )
            logs.append(f"Name: {row[0]} scheduled at {datetime.datetime.fromtimestamp(trigger_ts, tz=SG_TZ).strftime('%H%M')}")

    print("\n".join(logs))

    await asyncio.gather(*tasks)

    print("Job completed")
    print("-------------")


# Assuming no midnight crossing
def random_trigger_timestamp(start_hour, start_min, end_hour, end_min):
    today = datetime.datetime.now(SG_TZ).date()

    start_dt = datetime.datetime.combine(
        today,
        datetime.time(int(start_hour), int(start_min)),
        tzinfo=SG_TZ
    )
    end_dt = datetime.datetime.combine(
        today,
        datetime.time(int(end_hour), int(end_min)),
        tzinfo=SG_TZ
    )

    start_ts = start_dt.timestamp()
    end_ts = end_dt.timestamp()

    return random.uniform(start_ts, end_ts)


async def process_user(row, trigger_ts):
    # Wait until this user's scheduled time
    delay = max(0, trigger_ts - time.time())
    await asyncio.sleep(delay)

    async with semaphore:
        try:
            print(f"Submitting form for {row[0]}...")
            await send_message(user_id=row[3], message=f"Submitting form for {row[0]}...")
            await fill_and_submit(row[0], row[1])
            await asyncio.sleep(20)
            invitation_link = get_invitation_link(row[0])
            print(f"Invitation link for {row[0]}: {invitation_link}")
            await upload_photo(invitation_link, row[3])
            await send_message(
                user_id=row[3],
                message=f"You can now use facial recognition at the gantry. Alternatively, access your QR code <a href='{invitation_link}'>here</a>.",
                parse_mode="HTML"
            )

            with get_conn() as conn:
                conn.execute("""
                    INSERT INTO job_run (user_id, status, name, email, face_photo_path, error)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                             (row[3], "Successful", row[0], row[1], row[2], ""))
        except Exception as e:
            await send_message(user_id=row[3], message=f"❌ Error: {e}")
            print(f"❌ Error: {e}")

            with get_conn() as conn:
                conn.execute("""
                    INSERT INTO job_run (user_id, status, name, email, face_photo_path, error)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                             (row[3], "Failed", row[0], row[1], row[2], str(e)))


async def send_message(user_id, message, parse_mode=None):
    bot = Bot(TELEGRAM_BOT_TOKEN)
    await bot.send_message(chat_id=user_id, text=message, parse_mode=parse_mode)


def run_job():
    if (ALL_DAYS == "True") or datetime.datetime.now(SG_TZ).weekday() < 5:
        asyncio.run(job())


def start_daily_job():
    print(
        "Scheduler started...\n"
        f"All days: {ALL_DAYS == 'True'}\n"
        f"Max concurrent users: {MAX_CONCURRENT_USERS}\n"
        f"Early prep: {EARLY_PREP_JOB_HOUR}{EARLY_PREP_JOB_MIN}\n"
        f"Start: {START_JOB_HOUR}{START_JOB_MIN}\n"
        f"End: {END_JOB_HOUR}{END_JOB_MIN}\n"
        f"Now: {datetime.datetime.now().astimezone()}\n"
        f"Timezone: {datetime.datetime.now().astimezone().tzinfo}"
    )

    # Schedule the job daily at hh:mm:ss
    schedule.every().day.at(f"{EARLY_PREP_JOB_HOUR}:{EARLY_PREP_JOB_MIN}:00", TIMEZONE).do(run_job)

    # run_job()

    while True:
        schedule.run_pending()
        time.sleep(30)  # wait 30 seconds before checking again


if __name__ == "__main__":
    print("This only runs when executed directly")
    start_daily_job()
