from dotenv import load_dotenv
import os

# Load environment variables from the sample.env file
load_dotenv(dotenv_path="sample.env")

# Access environment variables
API_ID = os.getenv("27763335")
API_HASH = os.getenv("339bc57607286baa0d68a97a692329f0")
BOT_TOKEN = os.getenv("7661592174:AAGxGsJsO-6pck4NN7m_2uFmKoum2Yy52wM")
MONGO_URI = os.getenv("mongodb+srv://Teamsanki:Teamsanki@cluster0.jxme6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
CHANNEL_LINK = os.getenv("https://t.me/matalbi_duniya")
OWNER_ID = os.getenv("7877197608")
LOGGER_GROUP = os.getenv("-1002100433415")
