import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import pymongo
from datetime import datetime

# Configurations
API_ID = "27763335"  # Replace with your actual API_ID
API_HASH = "339bc57607286baa0d68a97a692329f0"  # Replace with your actual API_HASH
BOT_TOKEN = "7661592174:AAGxGsJsO-6pck4NN7m_2uFmKoum2Yy52wM"  # Replace with your actual Bot Token
MONGO_URI = "mongodb+srv://Teamsanki:Teamsanki@cluster0.jxme6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # Replace with your actual MongoDB URI
CHANNEL_LINK = "https://t.me/matalbi_duniya"  # Replace with your actual channel link
OWNER_ID = 7877197608  # Replace with the actual Owner ID
LOGGER_GROUP = -1002100433415  # Replace with your actual log group ID

logging.basicConfig(level=logging.INFO)

bot = Client("MovieBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# MongoDB Setup
client = pymongo.MongoClient(MONGO_URI)
db = client["telegram_movie_bot"]
download_links_collection = db["download_links"]
stats_collection = db["stats"]

# Start Command
@bot.on_message(filters.command("start"))
def start(client, message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    # Welcome message
    message.reply(
        f"Welcome to the Movie Bot, {user_name}!\nChoose your action:",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Owner Support", url=f"tg://user?id={OWNER_ID}")],
                [InlineKeyboardButton("Movies", callback_data="movies")],
                [InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)]  # Channel button for all users
            ]
        ),
    )

    # Log the user activity when they start the bot
    client.send_message(
        LOGGER_GROUP,
        f"🎥 **New User Started the Bot**:\n\n"
        f"👤 User: [{user_name}](tg://user?id={user_id})\n"
        f"🆔 User ID: {user_id}",
    )

# Movies Inline Keyboard
@bot.on_callback_query(filters.regex("movies"))
def movies_menu(client, query: CallbackQuery):
    query.message.edit_text(
        "Choose a movie to watch:",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Pushpa 2", callback_data="pushpa2")],
                [InlineKeyboardButton("Kanguva", callback_data="kanguva")],
                [InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)]  # Channel button for all users
            ]
        ),
    )

# Send Download Button for the Selected Movie
@bot.on_callback_query(filters.regex("pushpa2|kanguva"))
def movie_download(client, query: CallbackQuery):
    movie_name = "Pushpa 2" if query.data == "pushpa2" else "Kanguva"

    # Fetch the movie file link from the database
    movie_data = download_links_collection.find_one({"movie_name": movie_name})
    if movie_data:
        movie_file_link = movie_data["movie_file_link"]
    else:
        query.message.reply_text("Sorry, this movie is not available.")
        return

    # Send the download button
    query.message.edit_text(
        f"🎬 **{movie_name}**\nClick the button below to download the movie.",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Download", callback_data=f"download_{query.data}")]
            ]
        ),
    )

# Handle the Download Button and Start Timer
@bot.on_callback_query(filters.regex("download_pushpa2|download_kanguva"))
async def start_download_timer(client, query: CallbackQuery):
    movie_name = "Pushpa 2" if "pushpa2" in query.data else "Kanguva"

    # Acknowledge the user's click
    await query.answer("Download will start in 10 seconds...")

    # Edit the message to show the countdown
    for i in range(10, 0, -1):
        await query.message.edit_text(
            f"🎬 **{movie_name}**\nYour download will start in {i} seconds..."
        )
        await asyncio.sleep(1)

    # Fetch the movie file link from the database
    movie_data = download_links_collection.find_one({"movie_name": movie_name})
    if movie_data:
        movie_file_link = movie_data["movie_file_link"]
    else:
        await query.message.edit_text("Sorry, this movie is not available.")
        return

    # Send the movie file
    await query.message.reply_video(
        movie_file_link,
        caption=f"🎬 **{movie_name}**\nHere is your movie. Enjoy watching!"
    )

    # Log the download activity
    client.send_message(
        LOGGER_GROUP,
        f"🎥 **Movie Downloaded**:\n\n"
        f"👤 User: [{query.from_user.first_name}](tg://user?id={query.from_user.id})\n"
        f"🆔 User ID: {query.from_user.id}\n"
        f"📀 Movie: {movie_name}",
    )

    # Update the stats for the movie
    stats_collection.update_one(
        {"movie_name": movie_name},
        {"$inc": {"download_count": 1}},
        upsert=True
    )

# Add Movie Link Command
@bot.on_message(filters.command("addlink"))
def add_link(client, message):
    # Check if the user is the owner
    if message.from_user.id != OWNER_ID:
        message.reply("You are not authorized to use this command.")
        return

    # Ask for the movie name and link
    message.reply("Please send the movie name and its MP4 file link (separated by a space). Example: `Pushpa 2 http://example.com/movie.mp4`")

    # Wait for the owner to send the movie name and link
    @bot.on_message(filters.text)
    def store_movie_link(client, message):
        # Ensure the message is from the owner
        if message.from_user.id != OWNER_ID:
            return
        
        # Split the message into movie name and movie link
        try:
            movie_name, movie_file_link = message.text.split(" ", 1)
        except ValueError:
            message.reply("Invalid format. Please send the movie name and link separated by a space.")
            return

        # Store the movie name and file link in the database
        download_links_collection.insert_one({
            "movie_name": movie_name,
            "movie_file_link": movie_file_link,
            "added_by": OWNER_ID,
            "date_added": datetime.now()
        })

        message.reply(f"Movie `{movie_name}` link added successfully!")

# Stats Command (Movie Downloads)
@bot.on_message(filters.command("stats"))
def stats(client, message):
    if message.from_user.id != OWNER_ID:
        message.reply("You are not authorized to view the stats.")
        return

    # Fetch stats for each movie
    stats_message = "**Movie Download Stats:**\n"
    
    # Get stats for all movies
    for movie in download_links_collection.find():
        movie_name = movie["movie_name"]
        movie_stats = stats_collection.find_one({"movie_name": movie_name})
        download_count = movie_stats["download_count"] if movie_stats else 0
        stats_message += f"📀 **{movie_name}** Downloads: {download_count}\n"
    
    # Send the stats message
    message.reply_text(stats_message)

# Run the bot
bot.run()
