import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioVideoPiped
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
ASSISTANT_ID = 7912035011  # Replace with your assistant ID (ID of the bot used for streaming)

logging.basicConfig(level=logging.INFO)

bot = Client("MovieBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
pytgcalls = PyTgCalls(bot)

# MongoDB Setup
client = pymongo.MongoClient(MONGO_URI)
db = client["telegram_movie_bot"]
movies_collection = db["movies"]
download_links_collection = db["download_links"]

# Add Movie VC Link Command (Owner Only)
@bot.on_message(filters.command("addvc") & filters.user(OWNER_ID))
def add_vc_link(client, message):
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        message.reply("Usage: /addvc <Movie Name> <Link>")
        return

    movie_name = args[1]
    link = args[2]

    # Insert or update movie VC link in database
    movies_collection.update_one(
        {"movie_name": movie_name},
        {"$set": {"vc_link": link}},
        upsert=True
    )

    message.reply(f"✅ VC Link added for {movie_name}.")

# Add Movie Download Link Command (Owner Only)
@bot.on_message(filters.command("addlink") & filters.user(OWNER_ID))
def add_download_link(client, message):
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        message.reply("Usage: /addlink <Movie Name> <Download Link>")
        return

    movie_name = args[1]
    download_link = args[2]

    # Insert or update download link in the database
    download_links_collection.update_one(
        {"movie_name": movie_name},
        {"$set": {"download_link": download_link}},
        upsert=True
    )

    message.reply(f"✅ Download link added for {movie_name}.")

# Play VC Command (Play Movie in Voice Chat)
@bot.on_message(filters.command("playvc"))
def play_vc(client, message):
    args = message.text.split(maxsplit=2)
    if len(args) < 2:
        message.reply("Usage: /playvc <Movie Name>")
        return

    movie_name = args[1]
    movie = movies_collection.find_one({"movie_name": movie_name})

    if not movie or "vc_link" not in movie:
        message.reply(f"Movie '{movie_name}' not found or no VC link available.")
        return

    movie_link = movie["vc_link"]
    group_id = message.chat.id

    # Play movie in VC
    pytgcalls.join_group_call(
        chat_id=group_id,
        stream=AudioVideoPiped(movie_link),
        bot_id=ASSISTANT_ID  # Use assistant ID for the VC stream
    )

    # Log the play action to the logger group
    client.send_message(
        LOGGER_GROUP,
        f"🎥 **Movie Played in VC**:\n\n"
        f"👤 User: [{message.from_user.first_name}](tg://user?id={message.from_user.id})\n"
        f"🎬 Movie: {movie_name}\n"
        f"📌 Group: {message.chat.title} (ID: {group_id})",
    )
    message.reply(f"Playing {movie_name} in VC...")

# Start Command (Channel Check)
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
        message.reply(f"An error occurred: {str(e)}")
        return

    # Add user to database if not already added
    if not db.users.find_one({"user_id": user_id}):
        db.users.insert_one({"user_id": user_id, "name": user_name, "joined_at": datetime.utcnow()})

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

# Movie Quality Selector (Directly Sends Link)
@bot.on_callback_query(filters.regex("pushpa2|kanguva"))
def movie_quality(client, query: CallbackQuery):
    movie_name = "Pushpa 2" if query.data == "pushpa2" else "Kanguva"
    download_link_entry = download_links_collection.find_one({"movie_name": movie_name})

    if not download_link_entry or "download_link" not in download_link_entry:
        query.message.edit_text(f"Sorry, no download link available for {movie_name} yet.")
        return

    download_link = download_link_entry["download_link"]
    query.message.edit_text(
        f"Here is your download link for {movie_name}: \n{download_link}",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Back to Movies", callback_data="movies")]
            ]
        ),
    )

    # Log the movie download to the logger group
    client.send_message(
        LOGGER_GROUP,
        f"🎥 **Movie Downloaded**:\n\n"
        f"👤 User: [{query.from_user.first_name}](tg://user?id={query.from_user.id})\n"
        f"🎬 Movie: {movie_name}\n"
        f"🆔 User ID: {query.from_user.id}\n"
        f"🔗 Download Link: {download_link}",
    )

# Stats Command (Owner Only)
@bot.on_message(filters.command("stats") & filters.user(OWNER_ID))
def stats(client, message):
    total_users = db.users.count_documents({})
    pushpa_downloads = db.downloads.count_documents({"movie": "Pushpa 2"})
    kanguva_downloads = db.downloads.count_documents({"movie": "Kanguva"})

    message.reply(
        f"📊 **Bot Stats**:\n\n"
        f"👤 Total Users: {total_users}\n"
        f"🎬 Pushpa 2 Downloads: {pushpa_downloads}\n"
        f"🎬 Kanguva Downloads: {kanguva_downloads}"
    )

# Start the bot (blocking call)
if __name__ == "__main__":
    bot.run()  # This is a blocking call that will keep the bot running
