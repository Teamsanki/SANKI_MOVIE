import logging
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

# Start Command (Channel Check and Inline Channel Button)
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
                [InlineKeyboardButton("Pushpa 1", callback_data="pushpa1")],
                [InlineKeyboardButton("Kanguva", callback_data="kanguva")],
                [InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)]  # Channel button for all users
            ]
        ),
    )

# Movie Trailer Selector (Shows Video Link and Download Link from DB)
@bot.on_callback_query(filters.regex("pushpa1|kanguva"))
def movie_trailer(client, query: CallbackQuery):
    movie_name = "Pushpa 1" if query.data == "pushpa1" else "Kanguva"
    trailer_link = ""
    download_link = ""

    # Set the trailer link based on the movie selected
    if movie_name == "Pushpa 2":
        trailer_link = "https://firebasestorage.googleapis.com/v0/b/social-bite-skofficial.appspot.com/o/Private%2Ftrlir%2FPushpa%202%20-%20The%20Rule%20Trailer%20(Hindi)%20_%20Allu%20Arjun%20_%20Sukumar%20_%20Rashmika%20Mandanna%20_%20Fahadh%20Faasil%20_%20DSP%20-%20T-Series%20(1080p%2C%20h264%2C%20youtube).mp4?alt=media&token=090765bc-fade-451a-9e6f-2c27c7c8a0d7"  # Replace with actual trailer link
    elif movie_name == "Kanguva":
        trailer_link = "https://firebasestorage.googleapis.com/v0/b/social-bite-skofficial.appspot.com/o/Private%2Ftrlir%2FKanguva%20-%20Hindi%20Trailer%20%20Suriya%20%20Bobby%20Deol%20%20Devi%20Sri%20Prasad%20%20Siva%20%20Studio%20Green%20%20UV%20Creations.mp4?alt=media&token=c525079c-3e33-4252-94fb-c4eed4d594b0"  # Replace with actual trailer link

    # Fetch the download link from the database based on the movie name
    movie_data = download_links_collection.find_one({"movie_name": movie_name})
    if movie_data:
        download_link = movie_data["download_link"]
    else:
        download_link = "No download link available for this movie."

    # Send the trailer video
    query.message.edit_text(
        f"Here is the trailer for {movie_name}:",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Back to Movies", callback_data="movies")],
                [InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)]  # Channel button for all users
            ]
        ),
    )

    # Send the trailer video
    query.message.reply_video(
        trailer_link,
        caption=f"Enjoy the trailer for {movie_name}!",
    )

    # Send the download link after the trailer
    query.message.reply_text(
        f"🎬 **Download {movie_name}**: {download_link}",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Back to Movies", callback_data="movies")],
                [InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)]  # Channel button for all users
            ]
        ),
    )

    # Update the stats when a download link is clicked
    update_download_stats(movie_name)

    # Log the trailer view and download link view to the logger group
    client.send_message(
        LOGGER_GROUP,
        f"🎬 **Movie Trailer & Download Link Viewed**:\n\n"
        f"👤 User: [{query.from_user.first_name}](tg://user?id={query.from_user.id})\n"
        f"🎥 Movie: {movie_name}\n"
        f"🆔 User ID: {query.from_user.id}\n"
        f"🔗 Trailer Link: {trailer_link}\n"
        f"🔗 Download Link: {download_link}",
    )

# Update download stats in MongoDB
def update_download_stats(movie_name):
    # Check if stats exist for the movie
    movie_stats = stats_collection.find_one({"movie_name": movie_name})
    
    if movie_stats:
        # Increment the download count
        stats_collection.update_one(
            {"movie_name": movie_name},
            {"$inc": {"download_count": 1}}
        )
    else:
        # Create a new record for the movie with a download count of 1
        stats_collection.insert_one({"movie_name": movie_name, "download_count": 1})

# Command to view stats
@bot.on_message(filters.command("stats"))
def view_stats(client, message):
    # Retrieve stats from MongoDB
    pushpa_stats = stats_collection.find_one({"movie_name": "Pushpa 1"})
    kanguva_stats = stats_collection.find_one({"movie_name": "Kanguva"})

    # Prepare the stats message
    stats_message = "🎬 **Movie Download Stats**:\n\n"

    if pushpa_stats:
        stats_message += f"📀 **Pushpa 1** Downloads: {pushpa_stats['download_count']}\n"
    else:
        stats_message += "📀 **Pushpa 1** Downloads: 0\n"

    if kanguva_stats:
        stats_message += f"📀 **Kanguva** Downloads: {kanguva_stats['download_count']}\n"
    else:
        stats_message += "📀 **Kanguva** Downloads: 0\n"

    message.reply(stats_message)

# Command to add movie download links (Only owner can use this)
@bot.on_message(filters.command("addlink"))
def add_download_link(client, message):
    if message.from_user.id != OWNER_ID:
        message.reply("You are not authorized to use this command.")
        return
    
    try:
        movie_name = message.text.split()[1]
        trailer_link = message.text.split()[2]
        download_link = message.text.split()[3]

        # Store the movie links in the database
        download_links_collection.update_one(
            {"movie_name": movie_name},
            {"$set": {"trailer_link": trailer_link, "download_link": download_link}},
            upsert=True
        )

        message.reply(f"Links for {movie_name} have been successfully added!")
    except IndexError:
        message.reply("Usage: /addlink <movie_name> <trailer_link> <download_link>")

# Run the bot
bot.run()
