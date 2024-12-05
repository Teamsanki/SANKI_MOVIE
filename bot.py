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

# Stats Command
@bot.on_message(filters.command("stats"))
def stats(client, message):
    if message.from_user.id != OWNER_ID:
        message.reply("You are not authorized to view stats.")
        return

    # Fetch total bot users
    total_users = user_collection.count_documents({})

    # Fetch total deployments
    total_deployments = deployments_collection.find_one({"bot_deployed": True})["deployment_count"]

    message.reply(f"Total Users: {total_users}\nTotal Deployments: {total_deployments}")

# Callback Query Handler for Movie Options
@bot.on_callback_query(filters.regex("^movies$"))
async def show_movies(client, callback_query):
    await callback_query.answer()  # Acknowledge the callback
    await callback_query.message.edit_text(
        "🎬 Choose a movie to explore:",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Pushpa 2", callback_data="pushpa2")],
                [InlineKeyboardButton("Kanguva", callback_data="kanguva")],
                [InlineKeyboardButton("Back", callback_data="back")]
            ]
        ),
    )

# Handle Pushpa 2 Movie Button
@bot.on_callback_query(filters.regex("^pushpa2$"))
async def pushpa2_movie(client, callback_query):
    await callback_query.answer()  # Acknowledge the callback
    movie_info = movie_data["Pushpa 2"]

    # Send the movie file directly to the user as an attachment for download
    await client.send_document(
        chat_id=callback_query.from_user.id,
        document=movie_info['movie_file_link'],  # The direct MP4 file link
        caption="🎬 **Pushpa 2** - Here is your movie for download!",
    )
    
    # Send the trailer link if needed
    await callback_query.message.edit_text(
        f"🎬 **Pushpa 2**\n\n"
        f"Trailer: [Watch Trailer](<{movie_info['trailer_link']}>)",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Back", callback_data="movies")]
            ]
        ),
    )

# Handle Kanguva Movie Button
@bot.on_callback_query(filters.regex("^kanguva$"))
async def kanguva_movie(client, callback_query):
    await callback_query.answer()  # Acknowledge the callback
    movie_info = movie_data["Kanguva"]

    # Send the movie file directly to the user as an attachment for download
    await client.send_document(
        chat_id=callback_query.from_user.id,
        document=movie_info['movie_file_link'],  # The direct MP4 file link
        caption="🎬 **Kanguva** - Here is your movie for download!",
    )
    
    # Send the trailer link if needed
    await callback_query.message.edit_text(
        f"🎬 **Kanguva**\n\n"
        f"Trailer: [Watch Trailer](<{movie_info['trailer_link']}>)",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Back", callback_data="movies")]
            ]
        ),
    )

# Handle Back Button
@bot.on_callback_query(filters.regex("^back$"))
async def back_to_main(client, callback_query):
    await callback_query.answer()  # Acknowledge the callback
    await callback_query.message.edit_text(
        "Welcome back! Choose an action below:",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Movies", callback_data="movies")],
                [InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)],
            ]
        ),
    )

# Run the bot
bot.run()
