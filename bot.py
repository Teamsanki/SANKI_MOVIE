import random
import asyncio
from datetime import datetime, timedelta
from pymongo import MongoClient
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from PIL import Image, ImageDraw, ImageFont
import io

# --- Bot Config ---
TOKEN = "YOUR_BOT_TOKEN"  # <-- Replace this with your bot token
MONGO_URL = "YOUR_MONGO_URL"  # <-- Replace this with your MongoDB connection string
WELCOME_IMAGE_URL = "https://graph.org/file/c0e17724e66a68a2de3a6-5ff173af1d3498d9e7.jpg"  # <-- Replace with your welcome image

# --- MongoDB Setup ---
client = MongoClient(MONGO_URL)
db = client["wordseekbot"]
games_col = db["games"]
scores_col = db["scores"]

# --- Word List ---
WORDS = [
    # Add your words here
    'able', 'acid', 'aged', 'also', 'area', 'army', 'atom', 'aunt', 'away', 'axis',
    'baby', 'back', 'bake', 'ball', 'band', 'bank', 'barn', 'base', 'bath', 'bear',
    # ... (add more words as needed)
]

# --- Constants ---
IMAGE_SIZE = (250, 250)
FONT_SIZE = 20

# --- Format Feedback ---
def format_feedback(guess: str, correct_word: str) -> str:
    feedback = []
    for i in range(4):
        if guess[i] == correct_word[i]:
            feedback.append("🟩")
        elif guess[i] in correct_word:
            feedback.append("🟨")
        else:
            feedback.append("🟥")
    return ''.join(feedback)

# --- Build Summary ---
def build_summary(guesses: list[str], correct_word: str, hint: str) -> str:
    summary = ""
    for guess in guesses:
        feedback = format_feedback(guess, correct_word)
        summary += f"{feedback} `{guess}`\n"
    summary += f"\n_\"{hint}\"_\n"
    return summary

# --- /start welcome ---
async def send_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    keyboard = [[InlineKeyboardButton("Start Game", callback_data="/new")]]
    markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_photo(
        chat_id=chat.id,
        photo=WELCOME_IMAGE_URL,
        caption="Welcome to *Four Word*! Guess 4-letter words with color feedback.\nUse /new to begin. Owner @SANKINETWORK ",
        parse_mode="Markdown",
        reply_markup=markup
    )

# --- /new game ---
async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    word = random.choice(WORDS)
    hint = f"Starts with '{word[0]}'"

    games_col.update_one(
        {"chat_id": chat_id},
        {"$set": {
            "word": word,
            "hint": hint,
            "guesses": [],
            "start_time": datetime.utcnow()
        }},
        upsert=True
    )
    await update.message.reply_text("New game started! Guess the 4-letter word.")

# --- /stop game ---
async def stop_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    games_col.delete_one({"chat_id": chat_id})
    await update.message.reply_text("Game stopped. Use /new to start a new one.")

# --- Handle guesses ---
async def handle_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game = games_col.find_one({"chat_id": chat_id})
    if not game:
        return  # Game not running, ignore all messages

    user = update.effective_user
    text = update.message.text.lower()

    if not text.isalpha() or len(text) != 4:
        return

    if text not in WORDS:
        await update.message.reply_text("This word is not in my dictionary.")
        return

    correct_word = game["word"]
    guesses = game.get("guesses", [])

    if text in guesses:
        return

    guesses.append(text)
    games_col.update_one({"chat_id": chat_id}, {"$set": {"guesses": guesses}})
    feedback = format_feedback(text, correct_word)
    await update.message.reply_text(f"{feedback} {text}", parse_mode="Markdown")

    if text == correct_word:
        now = datetime.utcnow()

        scores_col.update_one(
            {"chat_id": chat_id, "user_id": user.id},
            {"$set": {"name": user.first_name, "updated": now}, "$inc": {"score": 12}},
            upsert=True
        )
        scores_col.update_one(
            {"chat_id": "global", "user_id": user.id},
            {"$set": {"name": user.first_name, "updated": now}, "$inc": {"score": 12}},
            upsert=True
        )

        summary = build_summary(guesses, correct_word, game.get("hint", ""))
        await update.message.reply_text(f"👻 *{user.first_name} guessed it right!*\n\n{summary}", parse_mode="Markdown")
        await context.bot.send_message(chat_id=chat_id, text=f"🎉 Congratulations *{user.first_name}*! 👻", parse_mode="Markdown")
        games_col.delete_one({"chat_id": chat_id})

# --- /leaderboard ---
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    keyboard = [
        [
            InlineKeyboardButton("📅 Today", callback_data=f"lb_today_{chat_id}"),
            InlineKeyboardButton("🏆 Overall", callback_data=f"lb_overall_{chat_id}"),
            InlineKeyboardButton("🌍 Global", callback_data="lb_global")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose a leaderboard:", reply_markup=reply_markup)

# --- Leaderboard callback ---
async def leaderboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("lb_today_"):
        chat_id = int(data.split("_")[2])
        since = datetime.utcnow() - timedelta(days=1)
        pipeline = [
            {"$match": {"chat_id": chat_id, "updated": {"$gte": since}}},
            {"$group": {"_id": "$user_id", "score": {"$max": "$score"}, "name": {"$first": "$name"}}},
            {"$sort": {"score": -1}},
            {"$limit": 10}
        ]
        results = list(scores_col.aggregate(pipeline))
        title = "📅 Today's Leaderboard"

    elif data.startswith("lb_overall_"):
        chat_id = int(data.split("_")[2])
        results = list(scores_col.find({"chat_id": chat_id}).sort("score", -1).limit(10))
        title = "🏆 Overall Leaderboard"

    elif data == "lb_global":
        results = list(scores_col.find({"chat_id": "global"}).sort("score", -1).limit(10))
        title = "🌍 Global Leaderboard"

    else:
        return

    if not results:
        await query.edit_message_text("No scores found.")
        return

    msg = f"__{title}__\n"
    for idx, row in enumerate(results, 1):
        msg += f"> {idx}. *{row['name']}* — {row['score']} pts\n"

    await query.edit_message_text(msg, parse_mode="Markdown")

# --- /search command ---
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Find a random opponent (this is a placeholder, implement your own logic)
    members = await context.bot.get_chat_members(chat_id)
    opponents = [member.user.id for member in members if member.user.id != user_id and member.user.is_bot is False]
    
    if not opponents:
        await update.message.reply_text("No opponents available.")
        return

    opponent_id = random.choice(opponents)

    await update.message.reply_text(f"Your opponent is: {opponent_id}. Starting in 10 seconds...")
    
    # Wait for 10 seconds
    await asyncio.sleep(10)

    # Start the game
    await start_search_game(update, context, user_id, opponent_id)

# --- Start the Game Logic ---
async def start_search_game(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, opponent_id: int):
    word = random.choice(WORDS)
    reversed_word = word[::-1]

    # Create an image with the reversed word
    image = Image.new('RGB', IMAGE_SIZE, color='white')
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    text_width, text_height = draw.textsize(reversed_word, font=font)
    draw.text(((IMAGE_SIZE[0] - text_width) / 2, (IMAGE_SIZE[1] - text_height) / 2), reversed_word, fill='black', font=font)

    # Save the image to a BytesIO object
    image_bytes = io.BytesIO()
    image.save(image_bytes, format='PNG')
    image_bytes.seek(0)

    # Send the image to both users
    await context.bot.send_photo(chat_id=user_id, photo=image_bytes)
    await context.bot.send_photo(chat_id=opponent_id, photo=image_bytes)

    # Start the rounds
    await play_rounds(update, context, user_id, opponent_id, word)

# --- Handle Rounds ---
async def play_rounds(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, opponent_id: int, correct_word: str):
    rounds = 10
    user_scores = {user_id: 0, opponent_id: 0}
    user_health = {user_id: 100, opponent_id: 100}
    round_counter = 0

    while round_counter < rounds:
        await asyncio.sleep(10)  # Wait for 10 seconds for responses

        # Check if both users responded
        # Implement your logic to check responses and update scores and health
        # If a user does not respond, mark them as AFK and reduce health

        round_counter += 1

    # Determine the winner and update scores
    winner = user_id if user_scores[user_id] > user_scores[opponent_id] else opponent_id
    await update.message.reply_text(f"The winner is: {winner}!")
    # Update scores in the database

# --- /profile command ---
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Fetch user profile from the database
    user_profile = scores_col.find_one({"user_id": user_id})

    if user_profile:
        health = user_profile.get("health", 100)
        score = user_profile.get("score", 0)
        await update.message.reply_text(f"Your health: {health}, Your score: {score}")
    else:
        await update.message.reply_text("Profile not found.")

# --- Main ---
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", send_welcome))
    app.add_handler(CommandHandler("new", new_game))
    app.add_handler(CommandHandler("stop", stop_game))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CallbackQueryHandler(leaderboard_callback, pattern=r"^lb_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_guess))

    print("Bot is running...")
    app.run_polling()
