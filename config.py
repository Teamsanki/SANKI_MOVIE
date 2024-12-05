from dotenv import load_dotenv
import os

# Load environment variables from the sample.env file
load_dotenv(dotenv_path="sample.env")

# Access environment variables
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
CHANNEL_LINK = os.getenv("CHANNEL_LINK")
OWNER_ID = os.getenv("OWNER_ID")
LOGGER_GROUP = os.getenv("LOGGER_GROUP")
