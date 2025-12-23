import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# 1. Setup Logging (This allows you to see errors in your Railway dashboard)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 2. Initialize Groq Client
# Ensure you add 'GROQ_API_KEY' to your Railway Variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)

# 3. Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **Welcome to LlamaPro AI!**\n\n"
        "I am a lightning-fast AI assistant powered by Llama 3.3.\n"
        "I can help you with:\n"
        "• 📝 Writing & Summarizing\n"
        "• 💻 Coding & Debugging\n"
        "• 🌍 Translation\n"
        "• 💡 General Questions\n\n"
        "Just send me a message to get started!"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

# 4. Message Handler (The AI Logic)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # 1. Show the 'typing...' status in Telegram
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # 2. Call the Groq API
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": "You are LlamaPro AI, a helpful, friendly, and concise Telegram assistant. "
                               "Use Markdown for formatting bold text or code blocks."
                },
                {"role": "user", "content": user_text}
            ],
            temperature=0.7,  # Balance between creative and factual
            max_tokens=1024   # Limit response length to save resources
        )
        
        # 3. Get the response text
        ai_response = completion.choices[0].message.content
        
        # 4. Send the response back to the user
        await update.message.reply_text(ai_response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        await update.message.reply_text(
            "⚠️ *System Error:* I'm having trouble connecting to my brain. "
            "Please try again in a moment.", 
            parse_mode='Markdown'
        )

# 5. Main Execution
if __name__ == '__main__':
    # Ensure you add 'TELEGRAM_TOKEN' to your Railway Variables
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TO8523309348:AAGn795nFi9wMBHEBCAkUav5TO1ffWfa36cKEN")
    
    if not TELEGRAM_TOKEN or not GROQ_API_KEY:
        print("CRITICAL ERROR: API Keys are missing in environment variables!")
    else:
        # Build the Telegram App
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        
        # Add Handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        
        print("LlamaPro AI is now running...")
        app.run_polling()