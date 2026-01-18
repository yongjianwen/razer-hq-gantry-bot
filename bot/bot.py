import asyncio
import os
from functools import partial

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters, ConversationHandler,
)

from db.db import get_conn
from fill_form_razer_async import fill_and_submit
from submit_photo_async import upload_photo
from .check_email import get_invitation_link

# Load environment variables
load_dotenv()
DATA_PATH = os.environ.get("DATA_PATH")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
FORM_URL = os.environ.get("FORM_URL")
EMAIL_INPUT = os.environ.get("EMAIL_INPUT")
ADMIN_ID = os.environ.get("ADMIN_ID")
START_JOB_HOUR = os.environ.get("START_JOB_HOUR")
START_JOB_MIN = os.environ.get("START_JOB_MIN")
END_JOB_HOUR = os.environ.get("END_JOB_HOUR")
END_JOB_MIN = os.environ.get("END_JOB_MIN")

# Constants
WAITING_NAME, WAITING_FACE = range(2)


def init_db():
    with get_conn() as conn:
        with open("./db/schema.sql", "r") as f:
            conn.executescript(f.read())


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        "Hi there! 👋\n\n"
        f"You can use the <a href='{FORM_URL}'>visitor registration form</a> to enter the Razer HQ building 🏢 via the main gantry\n\n"
        "But, it is troublesome to do it manually every day 😕\n",
        parse_mode="HTML"
    )
    await asyncio.sleep(5)
    await update.message.reply_text(
        "So here am I 🤖\n\n"
        f"I help you automate the form submission every weekday (Mon - Fri) between {START_JOB_HOUR}{START_JOB_MIN} and {END_JOB_HOUR}{END_JOB_MIN}!\n\n"
        "Unfortunately, I cannot yet distinguish between a working day and a public holiday"
    )
    await asyncio.sleep(5)
    await update.message.reply_text(
        "Now, you just need to give me your name ✏️ and a photo of you 😶‍🌫️\n\n"
        "✅ I don't require your email because I use a common email inbox for all submissions"
    )
    await asyncio.sleep(5)
    await update.message.reply_text(
        "Get started with these commands:\n"
        "/set_name - set your name\n"
        "/set_face - set your face photo\n"
        "/generate - submit form now\n"
        "/toggle - toggle daily job\n\n"
        "You can also find them in the menu"
    )
    await update.message.reply_text(
        "Raise any issues @ <a href='https://github.com/yongjianwen/razer-hq-gantry-bot'>GitHub</a>\n"
        "Use at your own risk",
        parse_mode="HTML"
    )


async def set_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me your name")
    return WAITING_NAME


async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = update.message.text

    with get_conn() as conn:
        conn.execute("""
            INSERT INTO user (id, username, name, email)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                username = excluded.username,
                name = excluded.name,
                email = excluded.email,
                updated_at = CURRENT_TIMESTAMP
        """,
                     (user.id, user.username or "", name, EMAIL_INPUT))

        row = conn.execute("""
            SELECT name, email, face_photo_path
            FROM user
            WHERE id = ?
        """,
                           (user.id,)).fetchone()

    await update.message.reply_text(f"✅ Name saved")

    if row is None or not row[0] or not row[1] or not row[2]:
        pass
    else:
        with get_conn() as conn:
            job_row = conn.execute("""
                SELECT *
                FROM job
                WHERE id = ?
            """,
                                   (user.id,)).fetchone()

        if job_row is None:
            with get_conn() as conn:
                conn.execute("""
                    INSERT INTO job (id, active)
                    VALUES (?, 1)
                    ON CONFLICT(id) DO UPDATE SET
                        updated_at = CURRENT_TIMESTAMP
                """,
                             (user.id,))

            await update.message.reply_text(
                "✅ Daily automation enabled\n"
                f"I will help you to submit the form every weekday between {START_JOB_HOUR}{START_JOB_MIN} ~ {END_JOB_HOUR}{END_JOB_MIN}!"
            )

    return ConversationHandler.END


async def reject_invalid_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("That... doesn't look like a name")
    return WAITING_NAME


async def reject_non_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please send text only")
    return WAITING_NAME


async def set_face(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a picture of you")
    return WAITING_FACE


async def receive_face(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Photos are sent as a list of sizes (small → large)
    photo = update.message.photo[-1]  # Get the highest resolution
    file = await photo.get_file()

    os.makedirs(f"{DATA_PATH}/images", exist_ok=True)
    image_path = f"{DATA_PATH}/images/{update.effective_user.id}.jpg"
    await file.download_to_drive(image_path)

    with get_conn() as conn:
        conn.execute("""
            INSERT INTO user (id, username, email, face_photo_path)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                username = excluded.username,
                email = excluded.email,
                face_photo_path = excluded.face_photo_path,
                updated_at = CURRENT_TIMESTAMP
        """,
                     (user.id, user.username or "", EMAIL_INPUT, image_path))

        row = conn.execute("""
            SELECT name, email, face_photo_path
            FROM user
            WHERE id = ?
        """,
                           (user.id,)).fetchone()

    await update.message.reply_text("✅ Face photo saved")

    if row is None or not row[0] or not row[1] or not row[2]:
        pass
    else:
        with get_conn() as conn:
            job_row = conn.execute("""
                SELECT *
                FROM job
                WHERE id = ?
            """,
                                   (user.id,)).fetchone()

        if job_row is None:
            with get_conn() as conn:
                conn.execute("""
                    INSERT INTO job (id, active)
                    VALUES (?, 1)
                    ON CONFLICT(id) DO UPDATE SET
                        updated_at = CURRENT_TIMESTAMP
                """,
                             (user.id,))

            await update.message.reply_text(
                "✅ Daily automation enabled\n"
                f"I will help you to submit the form every weekday between {START_JOB_HOUR}{START_JOB_MIN} ~ {END_JOB_HOUR}{END_JOB_MIN}!"
            )

    return ConversationHandler.END


async def reject_non_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please send image only")
    return WAITING_FACE


async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    with get_conn() as conn:
        row = conn.execute("""
            SELECT name, email, face_photo_path
            FROM user
            WHERE id = ?
        """,
                           (user.id,)).fetchone()

    if row is None or not row[0] or not row[1]:
        await update.message.reply_text("Please set your name using /set_name")
    elif not row[2]:
        await update.message.reply_text("Please set your face photo using /set_face")
    else:
        await update.message.reply_text(f"Submitting form for {row[0]}...")
        try:
            await fill_and_submit(row[0], row[1])
            await asyncio.sleep(20)
            invitation_link = get_invitation_link(row[0])
            await upload_photo(invitation_link, user.id)
            await update.message.reply_text(
                f"You can now use facial recognition at the gantry. Alternatively, access your QR code <a href='{invitation_link}'>here</a>.",
                parse_mode="HTML"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
            print(f"❌ Error: {e}")

    return ConversationHandler.END


async def toggle_job(update: Update, context: ContextTypes.DEFAULT_TYPE, active: int = None):
    user = update.effective_user

    with get_conn() as conn:
        row = conn.execute("""
            SELECT u.name, u.face_photo_path, j.active
            FROM user u
            LEFT JOIN job j ON j.id = u.id
            WHERE u.id = ?
        """,
                           (user.id,)).fetchone()

    if row is None or not row[0]:
        await update.message.reply_text("Please set your name using /set_name")
        return
    elif not row[1]:
        await update.message.reply_text("Please set your face photo using /set_face")
        return

    if active is None:
        new_active = 1 if row[2] == 0 else 0
    elif active == row[2] and active == 1:
        await update.message.reply_text("Daily job already resumed")
        return
    elif active == row[2] and active == 0:
        await update.message.reply_text("Daily job already paused")
        return
    else:
        new_active = active

    with get_conn() as conn:
        conn.execute("""
            UPDATE job
            SET active = ?
            WHERE id = ?
        """,
                     (new_active, user.id,))

    if new_active:
        await update.message.reply_text(
            "Daily job resumed until you /pause\n\n"
            f"<b>Name:</b> {row[0]}\n"
            "<b>Photo:</b> ✅ Yes",
            parse_mode="HTML"
        )
        # await update.message.reply_photo(photo=open(f"{DATA_PATH}/images/{user.id}.jpg", "rb"))
    else:
        await update.message.reply_text("Daily job paused until you /resume")


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    with get_conn() as conn:
        conn.execute("DELETE FROM user WHERE id = ?", (user.id,))
        conn.execute("DELETE FROM job WHERE id = ?", (user.id,))
        conn.execute("DELETE FROM job_run WHERE user_id = ?", (user.id,))

    await update.message.reply_text("Cleared")


async def clear_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if str(user.id) != ADMIN_ID:
        await update.message.reply_text("401: Unauthorized")
        return

    with get_conn() as conn:
        conn.execute("DELETE FROM user")
        conn.execute("DELETE FROM job")
        conn.execute("DELETE FROM job_run")

    await update.message.reply_text("Cleared all")


async def announce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if str(user.id) != ADMIN_ID:
        await update.message.reply_text("401: Unauthorized")
        return

    message = " ".join(context.args)

    if not message:
        await update.message.reply_text("Usage: /announce <message>")
        return

    with get_conn() as conn:
        rows = conn.execute("SELECT id FROM user").fetchall()

    for row in rows:
        await context.bot.send_message(chat_id=row[0], text=message)

    await update.message.reply_text("Ok")


def main():
    print("Starting bot...")

    init_db()

    app = ApplicationBuilder() \
        .token(TELEGRAM_BOT_TOKEN) \
        .concurrent_updates(True) \
        .build()

    name_filter = filters.Regex(r"^[A-Za-z\u4e00-\u9fff ]{1,100}$")

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("set_name", set_name),
            CommandHandler("set_face", set_face),
        ],
        states={
            WAITING_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & name_filter, receive_name),
                MessageHandler(filters.TEXT & ~filters.COMMAND, reject_invalid_name),
                MessageHandler(~filters.TEXT, reject_non_text),
            ],
            WAITING_FACE: [
                MessageHandler(filters.PHOTO, receive_face),
                MessageHandler(~filters.PHOTO & ~filters.COMMAND, reject_non_image),
            ],
        },
        fallbacks=[
            CommandHandler("set_name", set_name),
            CommandHandler("set_face", set_face),
        ]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("generate", generate))
    app.add_handler(CommandHandler("toggle", partial(toggle_job)))
    app.add_handler(CommandHandler("pause", partial(toggle_job, active=0)))
    app.add_handler(CommandHandler("resume", partial(toggle_job, active=1)))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("clear_all", clear_all))
    app.add_handler(CommandHandler("announce", announce))
    app.add_handler(conv_handler)

    app.run_polling()


if __name__ == "__main__":
    print("This only runs when executed directly")
    main()
