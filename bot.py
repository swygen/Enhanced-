import os, io, datetime, requests
from PIL import Image, ImageEnhance
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, CallbackQueryHandler, filters
from keep_alive import keep_alive

# Optional rembg import
try:
    from rembg import remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

# === CONFIG ===
BOT_TOKEN = "7410660233:AAGZPtovYR7kd1Nm0n1_bpNERZ7mJ56hYzs"
GROUP_ID = -1002572781690
REMOVE_BG_API_KEY = "jzesLG1RQJkZ2k2i3SZvDdhM"
user_usage = {}

# === START HANDLER ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        member = await context.bot.get_chat_member(GROUP_ID, user.id)
    except:
        member = None

    if not member or member.status not in ["member", "administrator", "creator"]:
        await update.message.reply_text("দয়া করে আমাদের গ্রুপে যোগ দিন:\nhttps://t.me/swygenbd")
        return

    keyboard = [
        [InlineKeyboardButton("Upload Image", callback_data="upload_image")],
        [InlineKeyboardButton("Developer Info", url="https://t.me/Swygen_bd")]
    ]
    await update.message.reply_text(
        f"স্বাগতম {user.first_name}! নীচের অপশনগুলো ব্যবহার করুন:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# === CALLBACK BUTTON HANDLER ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "upload_image":
        context.user_data["awaiting_image"] = True
        await query.message.reply_text("ছবিটি পাঠান, এরপর আপনাকে অপশন দেওয়া হবে।")
        return

    if query.data in ["enhance", "remove_bg", "hd_quality"]:
        file = context.user_data.get("image_file")
        if not file:
            await query.message.reply_text("ছবি পাওয়া যায়নি, অনুগ্রহ করে আবার চেষ্টা করুন।")
            return

        img_bytes = await file.download_as_bytearray()
        image = Image.open(io.BytesIO(img_bytes)).convert("RGBA")

        if query.data == "enhance":
            enhancer = ImageEnhance.Sharpness(image)
            result = enhancer.enhance(2.0)

        elif query.data == "remove_bg":
            if REMOVE_BG_API_KEY:
                response = requests.post(
                    "https://api.remove.bg/v1.0/removebg",
                    files={"image_file": io.BytesIO(img_bytes)},
                    data={"size": "auto"},
                    headers={"X-Api-Key": REMOVE_BG_API_KEY},
                )
                result = Image.open(io.BytesIO(response.content))
            elif REMBG_AVAILABLE:
                result = remove(image)
            else:
                await query.message.reply_text("rembg ইনস্টল করা নেই বা remove.bg API Key পাওয়া যায়নি।")
                return

        elif query.data == "hd_quality":
            response = requests.post(
                "https://api.deepai.org/api/torch-srgan",
                files={'image': io.BytesIO(img_bytes)},
                headers={'api-key': 'quickstart-QUdJIGlzIGNvbWluZy4uLi4K'},
            )
            output_url = response.json().get("output_url")
            await query.message.reply_photo(photo=output_url, caption="আপনার ছবি HD কোয়ালিটিতে রূপান্তরিত হয়েছে!")
            return

        output_io = io.BytesIO()
        result.save(output_io, format='PNG')
        output_io.seek(0)

        feedback_btn = [[InlineKeyboardButton("Feedback দিন", url="https://t.me/Swygen_bd")]]
        await query.message.reply_photo(
            photo=output_io,
            caption="আপনার ছবি তৈরি!",
            reply_markup=InlineKeyboardMarkup(feedback_btn)
        )

# === PHOTO RECEIVER ===
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    today = datetime.date.today()

    if user_id not in user_usage or user_usage[user_id]["date"] != today:
        user_usage[user_id] = {"count": 0, "date": today}

    if user_usage[user_id]["count"] >= 5:
        await update.message.reply_text("আপনার আজকের ৫টি লিমিট শেষ। কাল আবার চেষ্টা করুন।")
        return

    if context.user_data.get("awaiting_image"):
        context.user_data["image_file"] = await update.message.photo[-1].get_file()
        context.user_data["awaiting_image"] = False
        user_usage[user_id]["count"] += 1

        keyboard = [
            [InlineKeyboardButton("Enhanced", callback_data="enhance")],
            [InlineKeyboardButton("Remove BG", callback_data="remove_bg")],
            [InlineKeyboardButton("HD Quality", callback_data="hd_quality")]
        ]
        await update.message.reply_text("ছবির জন্য একটি অপশন নির্বাচন করুন:", reply_markup=InlineKeyboardMarkup(keyboard))

# === MAIN RUN ===
if __name__ == "__main__":
    keep_alive()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()
