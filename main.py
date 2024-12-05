import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped
import pymongo
from datetime import datetime

# Configurations
from config import API_ID, API_HASH, BOT_TOKEN, MONGO_URI, CHANNEL_LINK, OWNER_ID, LOGGER_GROUP
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
async def add_link(client, message):
    args = message.text.split(maxsplit=3)
    if len(args) < 4:
        await message.reply("Usage: /addlink <Movie Name> <Quality> <Link>")
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

    await message.reply(f"✅ Link added for {movie_name} ({quality}).")

@bot.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    # Channel join check
    if not await client.get_chat_member(CHANNEL_LINK.split('/')[-1], user_id):
        await message.reply(
            "Please join our channel to use the bot!",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)]]
            ),
        )
        return

    # Add user to database if not already added
    if not users_collection.find_one({"user_id": user_id}):
        users_collection.insert_one({"user_id": user_id, "name": user_name, "joined_at": datetime.utcnow()})

    # Welcome message and photo
    photo_url = "https://example.com/photo.jpg"  # Replace with your image URL
    await message.reply_photo(
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
async def movies_menu(client, query: CallbackQuery):
    await query.message.edit_text(
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
async def movie_quality(client, query: CallbackQuery):
    movie_name = "Pushpa 2" if query.data == "pushpa2" else "Kanguva"
    await query.message.edit_text(
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
async def send_movie(client, query: CallbackQuery):
    data = query.data.split("_")
    movie_name = "Pushpa 2" if "pushpa2" in data[0] else "Kanguva"
    quality = data[1]

    movie = movies_collection.find_one({"movie_name": movie_name})
    if not movie:
        await query.message.reply("Movie not found!")
        return

    movie_link = movie["links"].get(quality)
    if not movie_link:
        await query.message.reply("Requested quality not available!")
        return

    downloads_collection.insert_one({"user_id": query.from_user.id, "movie": movie_name, "quality": quality, "timestamp": datetime.utcnow()})

    await query.message.reply_document(
        document=movie_link,
        caption=f"Here is your movie: {movie_name} ({quality})"
    )

# Play VC Command
@bot.on_message(filters.command("playvc"))
async def play_vc(client, message):
    args = message.text.split(maxsplit=2)
    if len(args) < 2:
        await message.reply("Usage: /playvc <Movie Name>")
        return

    movie_name = args[1]
    movie = movies_collection.find_one({"movie_name": movie_name})
    if not movie or "1080p" not in movie["links"]:
        await message.reply("Movie or 1080p quality not found!")
        return

    movie_link = movie["links"]["1080p"]
    group_id = message.chat.id

    await pytgcalls.join_group_call(
        chat_id=group_id,
        stream=AudioVideoPiped(movie_link)
    )

    await client.send_message(
        LOGGER_GROUP,
        f"🎥 **Movie Played in VC**:\n\n"
        f"👤 User: [{message.from_user.first_name}](tg://user?id={message.from_user.id})\n"
        f"🎬 Movie: {movie_name}\n"
        f"📌 Group: {message.chat.title} (ID: {group_id})",
    )
    await message.reply(f"Playing {movie_name} in VC (1080p)...")

# Stop VC Command
@bot.on_message(filters.command("stopvc"))
async def stop_vc(client, message):
    group_id = message.chat.id
    await pytgcalls.leave_group_call(chat_id=group_id)
    await message.reply("Stopped playing in VC.")

# Stats Command
@bot.on_message(filters.command("stats") & filters.user(OWNER_ID))
async def stats(client, message):
    total_users = users_collection.count_documents({})
    pushpa_downloads = downloads_collection.count_documents({"movie": "Pushpa 2"})
    kanguva_downloads = downloads_collection.count_documents({"movie": "Kanguva"})

    await message.reply(
        f"📊 **Bot Stats**:\n\n"
        f"👤 Total Users: {total_users}\n"
        f"🎬 Pushpa 2 Downloads: {pushpa_downloads}\n"
        f"🎬 Kanguva Downloads: {kanguva_downloads}"
    )

# Start PyTgCalls
pytgcalls.start()
bot.run()
