import random
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

# --- Bot Config ---
TOKEN = "7364490758:AAFQHSTWOfFxxebzOpP_O_lLakaYPLYNkDo"  # <-- Replace this with your bot token
MONGO_URL = "mongodb+srv://TSANKI:TSANKI@cluster0.u2eg9e1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # <-- Replace this with your MongoDB connection string
WELCOME_IMAGE_URL = "https://graph.org/file/c0e17724e66a68a2de3a6-5ff173af1d3498d9e7.jpg"  # <-- Replace with your welcome image

# --- MongoDB Setup ---
client = MongoClient(MONGO_URL)
db = client["wordseekbot"]
games_col = db["games"]
scores_col = db["scores"]

# --- Word List ---
WORDS = [
    # A
    'able', 'acid', 'aged', 'also', 'area', 'army', 'atom', 'aunt', 'away', 'axis', 'amit', 'dick', 'slap', 'crow',
    # B
    'baby', 'back', 'bake', 'ball', 'band', 'bank', 'barn', 'base', 'bath', 'bear',
    'beat', 'been', 'bell', 'belt', 'bend', 'best', 'bike', 'bill', 'bird', 'bite',
    'blue', 'boat', 'body', 'bomb', 'bond', 'bone', 'book', 'boom', 'boot', 'bore',
    'born', 'boss', 'both', 'bowl', 'brag', 'bray', 'bred', 'brew', 'brim', 'buck',
    'buff', 'bulk', 'bull', 'bump', 'burn', 'bush', 'busy', 'buzz', 'byte',
    # C
    'cage', 'cake', 'call', 'calm', 'camp', 'card', 'care', 'cart', 'case', 'cash',
    'cast', 'cave', 'cell', 'chat', 'chip', 'city', 'clay', 'club', 'coal', 'coat',
    'cold', 'come', 'cook', 'cool', 'cope', 'cord', 'core', 'cost', 'crew', 'crop',
    'curl', 'cute', 'chill'
    # D
    'dark', 'data', 'date', 'dawn', 'deal', 'debt', 'deep', 'deer', 'desk', 'dial',
    'dice', 'died', 'diet', 'dime', 'dine', 'dish', 'disk', 'dive', 'dock', 'does',
    'doge', 'dome', 'done', 'doom', 'door', 'dose', 'down', 'drag', 'draw', 'drop',
    'drum', 'dual', 'duck', 'duke', 'dull', 'dust', 'duty',
    # E
    'each', 'earn', 'ease', 'east', 'easy', 'edge', 'edit', 'else', 'envy', 'epic',
    'even', 'ever', 'evil', 'exam', 'exit', 'eyes',
    # F
    'face', 'fact', 'fade', 'fail', 'fair', 'fake', 'fall', 'fame', 'farm', 'fast',
    'fate', 'fear', 'feed', 'feel', 'feet', 'fell', 'felt', 'file', 'fill', 'film',
    'find', 'fine', 'fire', 'firm', 'fish', 'fist', 'five', 'flag', 'flat', 'flip',
    'flow', 'fold', 'folk', 'food', 'foot', 'form', 'fort', 'four', 'free', 'frog',
    'fuel', 'full', 'fund', 'fuse',
    # G
    'gain', 'game', 'gang', 'gate', 'gave', 'gear', 'gene', 'gift', 'girl', 'give',
    'glad', 'goal', 'goat', 'gold', 'golf', 'gone', 'good', 'grab', 'gray', 'grew',
    'grid', 'grim', 'grip', 'grow', 'gulf', 'guts',
    # H
    'hair', 'half', 'hall', 'hand', 'hang', 'hard', 'harm', 'hate', 'have', 'hawk',
    'head', 'heal', 'heap', 'hear', 'heat', 'held', 'hell', 'help', 'herb', 'hero',
    'hide', 'high', 'hill', 'hire', 'hold', 'hole', 'holy', 'home', 'hope', 'horn',
    'host', 'hour', 'huge', 'hung', 'hunt', 'hurt',
    # I
    'idea', 'idle', 'inch', 'into', 'iron', 'item',
    # J
    'jack', 'jade', 'jail', 'jazz', 'jeep', 'jest', 'join', 'joke', 'jump', 'jury',
    # K
    'keep', 'kept', 'kick', 'kill', 'kind', 'king', 'kiss', 'kite', 'knee', 'knew',
    'knit', 'know',
    # L
    'lack', 'lady', 'lake', 'lamp', 'land', 'lane', 'last', 'late', 'lava', 'lazy',
    'lead', 'leaf', 'left', 'lend', 'less', 'life', 'lift', 'like', 'limb', 'line',
    'link', 'lion', 'list', 'live', 'load', 'loan', 'lock', 'logo', 'long', 'look',
    'loop', 'lord', 'lose', 'loss', 'lost', 'love', 'luck', 'lung',
    # M
    'made', 'mail', 'main', 'make', 'male', 'mall', 'many', 'mark', 'mask', 'mass',
    'mate', 'meal', 'mean', 'meat', 'meet', 'melt', 'menu', 'mere', 'mice', 'mild',
    'mile', 'milk', 'mill', 'mind', 'mine', 'mint', 'miss', 'mist', 'mode', 'mood',
    'moon', 'more', 'most', 'move', 'much', 'must', 'myth',
    # N
    'name', 'navy', 'near', 'neck', 'need', 'nest', 'news', 'next', 'nice', 'nick',
    'nine', 'node', 'none', 'noon', 'nose', 'note', 'noun', 'nuts',
    # O
    'oath', 'obey', 'omit', 'once', 'only', 'onto', 'open', 'oral', 'ours', 'oval',
    'oven', 'over', 'owed', 'own',
    # P
    'pack', 'page', 'paid', 'pain', 'pair', 'palm', 'park', 'part', 'pass', 'past',
    'path', 'peak', 'pear', 'peel', 'peer', 'peny', 'pick', 'pile', 'pill', 'pine',
    'pink', 'pipe', 'plan', 'play', 'plot', 'plug', 'plus', 'poem', 'pole', 'poll',
    'pond', 'pool', 'poor', 'port', 'post', 'pull', 'pure', 'push', 'pins', 
    # Q
    'quad', 'quiz', 'quit', 'quip',
    # R
    'race', 'rack', 'rage', 'raid', 'rail', 'rain', 'rank', 'rate', 'rays', 'read',
    'real', 'rear', 'redo', 'reed', 'reef', 'rest', 'rice', 'rich', 'ride', 'ring',
    'riot', 'rise', 'risk', 'road', 'rock', 'role', 'roof', 'room', 'root', 'rope',
    'rose', 'rule', 'rush', 'rust',
    # S
    'safe', 'said', 'sail', 'salt', 'same', 'sand', 'save', 'scan', 'scar', 'seal',
    'seat', 'seed', 'seek', 'seem', 'seen', 'self', 'sell', 'send', 'ship', 'shop',
    'shot', 'show', 'shut', 'side', 'sign', 'silk', 'sink', 'site', 'size', 'slip',
    'slow', 'snap', 'snow', 'soap', 'soft', 'soil', 'sold', 'sole', 'some', 'song',
    'soon', 'sort', 'soul', 'spot', 'star', 'stay', 'step', 'stop', 'such', 'suit', 'smag',
    'sure', 'swim', 'sync',
    # T
    'tail', 'take', 'tale', 'talk', 'tall', 'tank', 'tape', 'task', 'team', 'tear',
    'tech', 'tell', 'tend', 'tent', 'term', 'test', 'text', 'than', 'that', 'them',
    'then', 'they', 'thin', 'this', 'thus', 'time', 'tire', 'told', 'toll', 'tone',
    'tool', 'tops', 'torn', 'tour', 'town', 'trap', 'tree', 'trip', 'true', 'tube',
    'tune', 'turn', 'twin', 'type',
    # U
    'ugly', 'unit', 'urge', 'used', 'user', 'upon',
    # V
    'vain', 'vast', 'veil', 'verb', 'very', 'vest', 'view', 'vine', 'visa', 'vote',
    # W
    'wage', 'wait', 'wake', 'walk', 'wall', 'want', 'ward', 'warm', 'warn', 'wash',
    'wave', 'weak', 'wear', 'weed', 'week', 'well', 'west', 'what', 'when', 'whip',
    'wide', 'wife', 'wild', 'will', 'wind', 'wine', 'wing', 'wink', 'wipe', 'wire',
    'wise', 'wish', 'wolf', 'wood', 'word', 'worn', 'wrap', 'work',
    # X
    'xray',
    # Y
    'yard', 'yarn', 'yawn', 'yeah', 'year', 'yell', 'your', 'yoga',
    # Z
    'zero', 'zinc', 'zone', 'zoom'
]

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

# Global variable to store active users
active_users = set()

# --- /search command ---
async def search_opponent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Add the user to the active users set
    active_users.add(user_id)

    # Check if there are other active users to challenge
    if len(active_users) < 2:
        await update.message.reply_text("Waiting for another player to join. Please try again later.")
        return

    # Remove the current user from the list of potential opponents
    potential_opponents = list(active_users - {user_id})

    # Randomly select an opponent
    opponent_id = random.choice(potential_opponents)

    await context.bot.send_message(
        chat_id=opponent_id,
        text=f"You have been challenged by {update.effective_user.first_name} for a 1v1 match! Type /accept to join."
    )
    await update.message.reply_text(f"Challenged {opponent_id} for a 1v1 match!")

# --- /accept command ---
async def accept_challenge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if user_id not in active_users:
        await update.message.reply_text("You have not been challenged. Please wait for a challenge.")
        return

    # Logic to start the game goes here
    await update.message.reply_text("Challenge accepted! Starting the game...")

    # Initialize game state
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

    # Handle guesses
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
                {"$set": {"name": user.first_name, "updated": now}, "$inc": {"score": 25}},
                upsert=True
            )
            scores_col.update_one(
                {"chat_id": "global", "user_id": user.id},
                {"$set": {"name": user.first_name, "updated": now}, "$inc": {"score": 25}},
                upsert=True
            )

            summary = build_summary(guesses, correct_word, game.get("hint", ""))
            await update.message.reply_text(f"👻 *{user.first_name} guessed it right!*\n\n{summary}", parse_mode="Markdown")
            await context.bot.send_message(chat_id=chat_id, text=f"🎉 Congratulations *{user.first_name}*! 👻", parse_mode="Markdown")
            games_col.delete_one({"chat_id": chat_id})

    # Add handler for guesses
    
    # You can then initialize the game state here

# --- /leaderboard ---
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    keyboard = [
        [
            InlineKeyboardButton("🌍 Global", callback_data="lb_global"),
            InlineKeyboardButton("🏆 Overall", callback_data=f"lb_overall_{chat_id}")
        ],
        [
            InlineKeyboardButton("📅 Today", callback_data=f"lb_today_{chat_id}"),
            InlineKeyboardButton("🎮 Multiplayer", callback_data="lb_multiplayer")
        ],
        [
            InlineKeyboardButton("❌ Close", callback_data="close")
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

    elif data == "lb_multiplayer":
        results = list(scores_col.find({"chat_id": "multiplayer"}).sort("score", -1).limit(10))
        title = "🎮 Multiplayer Leaderboard"

    elif data == "close":
        await query.edit_message_text("Leaderboard closed.")
        return

    else:
        return

    if not results:
        await query.edit_message_text("No scores found.")
        return

    msg = f

# --- Main ---
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", send_welcome))
    app.add_handler(CommandHandler("new", new_game))
    app.add_handler(CommandHandler("stop", stop_game))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("search", search_opponent))
    app.add_handler(CommandHandler("accept", accept_challenge))  # New command# New command
    app.add_handler(CallbackQueryHandler(leaderboard_callback, pattern=r"^lb_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_guess))

    print("Bot is running...")
    app.run_polling()
