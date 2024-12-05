import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
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

# Start Command with Welcome Image
@bot.on_message(filters.command("start"))
def start(client, message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

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

    # Log the user activity
    client.send_message(
        LOGGER_GROUP,
        f"📥 **New User Started the Bot**\n\n"
        f"👤 User: [{user_name}](tg://user?id={user_id})\n"
        f"🆔 User ID: {user_id}",
    )

# Movies Menu with Photo
@bot.on_callback_query(filters.regex("movies"))
def movies_menu(client, query: CallbackQuery):
    # Edit the message to include a photo and menu
    query.message.edit_media(
        media=types.InputMediaPhoto(
            media="https://graph.org/file/8e4cde401593ac8ff61cb-ce171592c3ee5635c8.jpg",  # Replace with your image URL
            caption="🎬 **Choose a movie to watch or download:**"
        ),
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Pushpa 2", callback_data="pushpa2")],
                [InlineKeyboardButton("Kanguva", callback_data="kanguva")],
                [InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)],
            ]
        ),
    )
    
# Movie Details with Trailer Link
@bot.on_callback_query(filters.regex("pushpa2|kanguva"))
def movie_details(client, query: CallbackQuery):
    movie_name = "Pushpa 2" if query.data == "pushpa2" else "Kanguva"

    # Fetch movie details from the database
    movie_data = movies_collection.find_one({"movie_name": movie_name})
    if not movie_data:
        query.message.reply_text("Sorry, this movie is not available.")
        return

    # Prepare movie details
    movie_file_link = movie_data["movie_file_link"]
    trailer_link = movie_data.get("trailer_link", "Trailer not available")

    # Send movie details with a download button
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

    # Fetch the movie file link from the database
    movie_data = movies_collection.find_one({"movie_name": movie_name})
    if not movie_data:
        await query.message.edit_text("Sorry, this movie is not available.")
        return

    movie_file_link = movie_data["movie_file_link"]

    # Send the movie file
    await query.message.reply_video(
        movie_file_link,
        caption=f"🎬 **{movie_name}**\nHere is your movie. Enjoy watching!"
    )

    # Log the download
    client.send_message(
        LOGGER_GROUP,
        f"📥 **Movie Downloaded**\n\n"
        f"👤 User: [{query.from_user.first_name}](tg://user?id={query.from_user.id})\n"
        f"🆔 User ID: {query.from_user.id}\n"
        f"🎬 Movie: {movie_name}",
    )

    # Update movie stats
    stats_collection.update_one(
        {"movie_name": movie_name},
        {"$inc": {"download_count": 1}},
        upsert=True
    )

# Add Movie Command (For Owner)
@bot.on_message(filters.command("addlink"))
def add_movie(client, message):
    # Check if the user is the owner
    if message.from_user.id != OWNER_ID:
        message.reply("You are not authorized to use this command.")
        return

    message.reply("Send the movie name, MP4 file link, and trailer link in this format:\n"
                  "`Pushpa 2 <movie_file_link> <trailer_link>`")

    @bot.on_message(filters.text)
    def save_movie_details(client, message):
        # Ensure only the owner can send movie details
        if message.from_user.id != OWNER_ID:
            return

        # Parse the movie details
        try:
            parts = message.text.split(" ", 2)
            movie_name = parts[0]
            movie_file_link = parts[1]
            trailer_link = parts[2]
        except IndexError:
            message.reply("Invalid format. Please provide all details.")
            return

        # Save movie details to the database
        movies_collection.insert_one({
            "movie_name": movie_name,
            "movie_file_link": movie_file_link,
            "trailer_link": trailer_link,
            "added_by": OWNER_ID,
            "date_added": datetime.now()
        })

        message.reply(f"🎬 Movie `{movie_name}` has been added successfully!")

# Stats Command
@bot.on_message(filters.command("stats"))
def stats(client, message):
    if message.from_user.id != OWNER_ID:
        message.reply("You are not authorized to view stats.")
        return

    # Fetch stats
    stats_message = "**Movie Download Stats:**\n"
    for movie in movies_collection.find():
        movie_name = movie["movie_name"]
        stats = stats_collection.find_one({"movie_name": movie_name})
        download_count = stats["download_count"] if stats else 0
        stats_message += f"🎬 **{movie_name}**: {download_count} downloads\n"

    message.reply_text(stats_message)

# Run the bot
bot.run()
