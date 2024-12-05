import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pytgcalls import PyTgCalls
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
pytgcalls = PyTgCalls(bot)

# MongoDB Setup
client = pymongo.MongoClient(MONGO_URI)
db = client["telegram_movie_bot"]
users_collection = db["users"]
downloads_collection = db["downloads"]
movies_collection = db["movies"]

# Add Movie Link Command (Owner Only)
@bot.on_message(filters.command("addlink") & filters.user(OWNER_ID))
def add_link(client, message):
    args = message.text.split(maxsplit=3)
    if len(args) < 4:
        message.reply("Usage: /addlink <Movie Name> <Quality> <Link>")
        return

    movie_name = args[1]
    quality = args[2]
    link = args[3]

    movie = movies_collection.find_one({"movie_name": movie_name})
    if movie:
        movies_collection.update_one(
            {"movie_name": movie_name},
            {"$set": {f"links.{quality}": link}}
        )
    else:
        movies_collection.insert_one({"movie_name": movie_name, "links": {quality: link}})

    message.reply(f"✅ Link added for {movie_name} ({quality}).")

# Handle Start Command and Check Channel Membership
@bot.on_message(filters.command("start"))
def start(client, message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    # Check if user has joined the channel
    try:
        member = client.get_chat_member(CHANNEL_LINK.split('/')[-1], user_id)
        if member.status not in ["member", "administrator", "creator"]:
            message.reply(
                "Please join our channel to use the bot!",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)]]
                ),
            )
            return
    except Exception as e:
        if "CHAT_ADMIN_REQUIRED" in str(e):
            message.reply("I don't have admin rights in the channel. Please make me an admin to check your membership.")
        else:
            message.reply(f"An error occurred: {str(e)}")
        return

    # Add user to database if not already added
    if not users_collection.find_one({"user_id": user_id}):
        users_collection.insert_one({"user_id": user_id, "name": user_name, "joined_at": datetime.utcnow()})

    # Welcome message and photo
    photo_url = "https://graph.org/file/6c0db28a848ed4dacae56-93b1bc1873b2494eb2.jpg"  # Replace with your image URL
    message.reply_photo(
        photo=photo_url,
        caption=f"Welcome to the Movie Bot, {user_name}!\nChoose your action:",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Owner Support", url=f"tg://user?id={OWNER_ID}")],
                [InlineKeyboardButton("Movies", callback_data="movies")]
            ]
        ),
    )

    # Log the start action
    bot.send_message(
        LOGGER_GROUP,
        f"📥 **New User Started the Bot**:\n\n"
        f"👤 User: [{user_name}](tg://user?id={user_id})\n"
        f"📅 Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
    )

# Movies Inline Keyboard
@bot.on_callback_query(filters.regex("movies"))
def movies_menu(client, query: CallbackQuery):
    query.message.edit_text(
        "Choose a movie:",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Pushpa 2", callback_data="pushpa2")],
                [InlineKeyboardButton("Kanguva", callback_data="kanguva")]
            ]
        )
    )

# Movie Quality Selector
@bot.on_callback_query(filters.regex("pushpa2|kanguva"))
def movie_quality(client, query: CallbackQuery):
    movie_name = "Pushpa 2" if query.data == "pushpa2" else "Kanguva"
    query.message.edit_text(
        f"Select quality for {movie_name}:",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("1080p", callback_data=f"{query.data}_1080"),
                    InlineKeyboardButton("720p", callback_data=f"{query.data}_720"),
                    InlineKeyboardButton("480p", callback_data=f"{query.data}_480"),
                ]
            ]
        ),
    )

# Send Movie File via Link
@bot.on_callback_query(filters.regex("pushpa2_1080|pushpa2_720|pushpa2_480|kanguva_1080|kanguva_720|kanguva_480"))
def send_movie(client, query: CallbackQuery):
    data = query.data.split("_")
    movie_name = "Pushpa 2" if "pushpa2" in data[0] else "Kanguva"
    quality = data[1]

    movie = movies_collection.find_one({"movie_name": movie_name})
    if not movie:
        query.message.reply("Movie not found!")
        return

    movie_link = movie["links"].get(quality)
    if not movie_link:
        query.message.reply("Requested quality not available!")
        return

    downloads_collection.insert_one({"user_id": query.from_user.id, "movie": movie_name, "quality": quality, "timestamp": datetime.utcnow()})

    query.message.reply_document(
        document=movie_link,
        caption=f"Here is your movie: {movie_name} ({quality})"
    )

# Play VC Command - Owner Uploads Link
@bot.on_message(filters.command("playvc") & filters.user(OWNER_ID))
def play_vc(client, message):
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        message.reply("Usage: /playvc <Movie Name> <Quality>")
        return

    movie_name = args[1]
    quality = args[2]

    movie = movies_collection.find_one({"movie_name": movie_name})
    if not movie or quality not in movie["links"]:
        message.reply("Movie or specified quality not found!")
        return

    movie_link = movie["links"][quality]
    group_id = message.chat.id

    # Play the movie in the VC (Voice chat)
    pytgcalls.join_group_call(
        chat_id=group_id,
        stream=AudioVideoPiped(movie_link)
    )

    # Log the action in logger group
    bot.send_message(
        LOGGER_GROUP,
        f"🎥 **Movie Played in VC**:\n\n"
        f"👤 User: [{message.from_user.first_name}](tg://user?id={message.from_user.id})\n"
        f"🎬 Movie: {movie_name}\n"
        f"📌 Group: {message.chat.title} (ID: {group_id})",
    )
    message.reply(f"Playing {movie_name} ({quality}) in VC...")

# Stop VC Command
@bot.on_message(filters.command("stopvc"))
def stop_vc(client, message):
    group_id = message.chat.id
    pytgcalls.leave_group_call(chat_id=group_id)
    message.reply("Stopped playing in VC.")

# Stats Command
@bot.on_message(filters.command("stats") & filters.user(OWNER_ID))
def stats(client, message):
    total_users = users_collection.count_documents({})
    pushpa_downloads = downloads_collection.count_documents({"movie": "Pushpa 2"})
    kanguva_downloads = downloads_collection.count_documents({"movie": "Kanguva"})

    message.reply(
        f"Total Users: {total_users}\n"
        f"Pushpa 2 Downloads: {pushpa_downloads}\n"
        f"Kanguva Downloads: {kanguva_downloads}"
    )

# Start the bot
bot.run()
