import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
import pymongo
from datetime import datetime

# Configurations
API_ID = "27763335"  # Replace with your API ID
API_HASH = "339bc57607286baa0d68a97a692329f0"  # Replace with your API HASH
BOT_TOKEN = "7661592174:AAGxGsJsO-6pck4NN7m_2uFmKoum2Yy52wM"  # Replace with your Bot Token
MONGO_URI = "mongodb+srv://Teamsanki:Teamsanki@cluster0.jxme6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # MongoDB URI
CHANNEL_LINK = "https://t.me/matalbi_duniya"  # Your channel link
OWNER_ID = 7877197608  # Owner's Telegram ID
LOGGER_GROUP = -1002100433415  # Logger group ID

logging.basicConfig(level=logging.INFO)

bot = Client("MovieBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# MongoDB Setup
client = pymongo.MongoClient(MONGO_URI)
db = client["telegram_movie_bot"]
movies_collection = db["movies"]
stats_collection = db["stats"]
user_collection = db["users"]
deployments_collection = db["deployments"]

# Movie Data (Add movie file link and trailer link for both movies)
movie_data = {
    "Pushpa 2": {
        "movie_file_link": "https://video-downloads.googleusercontent.com/ADGPM2micKYSN26lUtrrrzGfpYoUrb5oOuK818ZfQqOMo7v2i9Y_3XizBaCEqu71l0242lV-zOXEDTMMfseAMsVJDG0fhtQOSHSmM9JSRm4F-amxbOCYdU9nKB4L6iv2sRPZwxjpoQ83e2PzSz2ZB_XP7ccpeB73EPbYcpyU2YdEyZY4qDKtd6uU5Stej0_1dP-my6MxLuR7fJ3xsx9HO4i1oRkixGDIDQ5OnCH6d4PmECANajVZm17mrAPPac3fijYDEexMROoGIwfpbhLQSjBBylWH2absZKt6aeEkQr06ZaSGbNUe3ELMv7qeh7LRB0Qi3_uEMwLxlQ28faR-u4dyIw4JSSmuBWWGY3DjURibIys0PT5mW1B1anbTDONsVCd06Cx-oBPhZAIAmctMKCtpEgyUnGS2FmV-_WyTXGmiWGUdobwaeuxT-ZjcrfJ__i61OyC2s3Uka82PCl1LZ8V4QprYqHoqpEAOJL4jOAUtWx4jiUrmsX7vZBa1C5H1cMoYn-87OD_6F6KuIutZZZ8z_I04b5SpOZuYlLZNSLSGmv-IbNxb7_g8L0tq3pcf1DhUggdxqr1Sz3tt7BjRiHUsuXv3PknIq7oSqLTe6myowmaTgAY_hykNbK0UijWqSPoa2sic2dmhyzgM1Ne7YOFYZh42nAvluwQsbji4Cgawq7rz3ypP0ukNQrZu58Yl7KIWxWm13cscXTxDy4-MCGrCuUZmXLrypYrMM1ZuGMmYEvdc4w0MKAQhKLSPDGoD8QsjhnCwxwAage1ymbCqk_7sG_-Wov3HBpJyJCD_U7gwdAsvUiW6kQgJnvdtpbU5SrWwj0TSd1_F9bG2g9-saCTqSdmBa-3YC8SCH7fBP7GLPKEU1j4QiZb8Ymgkc4P24Azm9dOIfSSpHNZztN2RjpGgiOB_CzM3kOk11pj_DGuBEUrbdZ4UA2tolJb0GRXDXCMU8OGsDtdxAREznt639HYBNMNMhP20y3A89ReWuiHUJrVxC4Bx9qrKzE0h8K1j-Myi67nygW7E5EDXl4GhxenH_Zkq7eCb7zFDPAsQfAyLvhvbTGmGId00v5jwJ-Anaw47eZ6Dhlu6",  # Replace with the actual movie file link
        "trailer_link": "https://firebasestorage.googleapis.com/v0/b/social-bite-skofficial.appspot.com/o/Private%2Ftrlir%2FPushpa%202%20-%20The%20Rule%20Trailer%20(Hindi)%20_%20Allu%20Arjun%20_%20Sukumar%20_%20Rashmika%20Mandanna%20_%20Fahadh%20Faasil%20_%20DSP%20-%20T-Series%20(1080p%2C%20h264%2C%20youtube).mp4?alt=media&token=090765bc-fade-451a-9e6f-2c27c7c8a0d7"  # Replace with the actual trailer link
    },
    "Kanguva": {
        "movie_file_link": "https://pixeldra.in/api/file/prD8PBCb?download",  # Replace with the actual movie file link
        "trailer_link": "https://firebasestorage.googleapis.com/v0/b/social-bite-skofficial.appspot.com/o/Private%2Ftrlir%2FKanguva%20-%20Hindi%20Trailer%20%20Suriya%20%20Bobby%20Deol%20%20Devi%20Sri%20Prasad%20%20Siva%20%20Studio%20Green%20%20UV%20Creations.mp4?alt=media&token=c525079c-3e33-4252-94fb-c4eed4d594b0"  # Replace with the actual trailer link
    }
}

# Start Command with Welcome Image
@bot.on_message(filters.command("start"))
def start(client, message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    # Record unique user interaction
    user_collection.update_one(
        {"user_id": user_id},
        {"$set": {"user_name": user_name, "last_interacted": datetime.now()}},
        upsert=True
    )

    # Send Welcome Image
    message.reply_photo(
        photo="https://graph.org/file/6c0db28a848ed4dacae56-93b1bc1873b2494eb2.jpg",  # Replace with your welcome image URL
        caption=f"🎉 Welcome to the Movie Bot, {user_name}!\n\n"
                f"Click below to explore movies or join our channel:",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Movies", callback_data="movies")],
                [InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)],
            ]
        ),
    )

    # Increment total deployments
    deployments_collection.update_one(
        {"bot_deployed": True},
        {"$inc": {"deployment_count": 1}},
        upsert=True
    )

    # Log the user activity
    client.send_message(
        LOGGER_GROUP,
        f"📥 **New User Started the Bot**\n\n"
        f"👤 User: [{user_name}](tg://user?id={user_id})\n"
        f"🆔 User ID: {user_id}",
    )

# Stats Command
@bot.on_message(filters.command("stats"))
def stats(client, message):
    if message.from_user.id != OWNER_ID:
        message.reply("You are not authorized to view stats.")
        return

    # Fetch total bot users
    total_users = user_collection.count_documents({})

    # Fetch movie download stats
    pushpa2_downloads = stats_collection.find_one({"movie_name": "Pushpa 2"})
    kanguva_downloads = stats_collection.find_one({"movie_name": "Kanguva"})
    pushpa2_count = pushpa2_downloads["download_count"] if pushpa2_downloads else 0
    kanguva_count = kanguva_downloads["download_count"] if kanguva_downloads else 0

    # Fetch total deployments
    deployments = deployments_collection.find_one({"bot_deployed": True})
    deployment_count = deployments["deployment_count"] if deployments else 0

    # Stats Message
    stats_message = f"**Bot Stats:**\n\n"
    stats_message += f"👥 **Total Users:** {total_users}\n"
    stats_message += f"🎬 **Pushpa 2 Downloads:** {pushpa2_count}\n"
    stats_message += f"🎬 **Kanguva Downloads:** {kanguva_count}\n"
    stats_message += f"🤖 **Total Bot Deployments:** {deployment_count}"

    message.reply_text(stats_message)

# Movie Details with Trailer Link
@bot.on_callback_query(filters.regex("pushpa2|kanguva"))
def movie_details(client, query: CallbackQuery):
    movie_name = "Pushpa 2" if query.data == "pushpa2" else "Kanguva"

    # Fetch movie details from the movie_data dictionary
    movie_details = movie_data.get(movie_name)
    if not movie_details:
        query.message.reply_text("Sorry, this movie is not available.")
        return

    movie_file_link = movie_details["movie_file_link"]
    trailer_link = movie_details["trailer_link"]

    # Send movie details with a download button and trailer link
    query.message.edit_text(
        f"🎬 **{movie_name}**\n\n"
        f"📹 [Watch Trailer]({trailer_link})\n\n"
        f"Click the button below to download the movie.",
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Download", callback_data=f"download_{query.data}")],
            ]
        ),
    )

# Download Timer and Movie File Delivery
@bot.on_callback_query(filters.regex("download_pushpa2|download_kanguva"))
async def start_download_timer(client, query: CallbackQuery):
    movie_name = "Pushpa 2" if "pushpa2" in query.data else "Kanguva"

    # Acknowledge the user's click
    await query.answer("Preparing your download...")

    # Countdown timer
    for i in range(10, 0, -1):
        await query.message.edit_text(
            f"🎬 **{movie_name}**\nYour download will start in {i} seconds..."
        )
        await asyncio.sleep(1)

    # Fetch the movie file link from the movie_data dictionary
    movie_details = movie_data.get(movie_name)
    if not movie_details:
        await query.message.edit_text("Sorry, this movie is not available.")
        return

    movie_file_link = movie_details["movie_file_link"]

    # Send the movie file (simulated by sending a link for now)
    await query.message.reply_text(
        f"🎬 **{movie_name}**\nHere is your movie download link:\n{movie_file_link}"
    )

    # Log the download
    client.send_message(
        LOGGER_GROUP,
        f"📥 **Movie Downloaded**\n\n"
        f"👤 User: [{query.from_user.first_name}](tg://user?id={query.from_user.id})\n"
        f"🆔 User ID: {query.from_user.id}\n"
        f"🎬 Movie: {movie_name}",
    )

    # Update movie download stats
    stats_collection.update_one(
        {"movie_name": movie_name},
        {"$inc": {"download_count": 1}},
        upsert=True
    )

# Add Movie Command (For Owner)
@bot.on_message(filters.command("addlink"))
def add_movie(client, message):
    if message.from_user.id != OWNER_ID:
        message.reply("You are not authorized to use this command.")
        return

    message.reply("Send the movie name, MP4 file link, and trailer link in this format:\n"
                  "`Pushpa 2 <movie_file_link> <trailer_link>`")

    @bot.on_message(filters.text)
    def save_movie_details(client, message):
        if message.from_user.id != OWNER_ID:
            return

        try:
            parts = message.text.split(" ", 2)
            movie_name = parts[0]
            movie_file_link = parts[1]
            trailer_link = parts[2]
        except IndexError:
            message.reply("Invalid format. Please provide all details.")
            return

        movies_collection.insert_one({
            "movie_name": movie_name,
            "movie_file_link": movie_file_link,
            "trailer_link": trailer_link,
            "added_by": OWNER_ID,
            "date_added": datetime.now(),
        })
        message.reply(f"Movie **{movie_name}** has been added successfully!")

# Run the bot
bot.run()
