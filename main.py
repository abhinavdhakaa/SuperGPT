import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.error import BadRequest
from groq import Groq

# 1. Configuration
logging.basicConfig(level=logging.INFO)
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# IMPORTANT: Add bot as Admin to this channel first!
CHANNEL_ID = "@YourChannelUsername" 
CHANNEL_URL = "https://t.me/YourChannelUsername"

# 2. Check Membership Logic
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except BadRequest:
        return False

# 3. /start and Verification Button
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if await is_subscribed(context.bot, user_id):
        await update.message.reply_text("✅ Welcome back, Guru! Memory is active. Ask me anything.")
    else:
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL)],
            [InlineKeyboardButton("🔄 Verify Membership", callback_data='verify')]
        ]
        await update.message.reply_text(
            "⚠️ **Access Locked!**\n\nYou must join our channel to use the Guru AI with memory.",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )

# 4. Handle "Verify" Button Click
async def verify_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await is_subscribed(context.bot, query.from_user.id):
        await query.edit_message_text("✅ Verified! You can now chat with me.")
    else:
        await query.answer("❌ You haven't joined yet!", show_alert=True)

# 5. AI Logic with Memory
async def handle_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Force Join Check
    if not await is_subscribed(context.bot, user_id):
        await start(update, context)
        return

    # Memory Management: Initialize user_data if empty
    if "history" not in context.user_data:
        context.user_data["history"] = [
            {"role": "system", "content": "You are Yes Guru Support. Remember student details and help them."}
        ]

    # Add user message to history
    user_msg = update.message.text
    context.user_data["history"].append({"role": "user", "content": user_msg})

    # Keep only last 10 messages to save memory
    if len(context.user_data["history"]) > 11:
        context.user_data["history"] = [context.user_data["history"][0]] + context.user_data["history"][-10:]

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=context.user_data["history"]
        )
        answer = completion.choices[0].message.content
        context.user_data["history"].append({"role": "assistant", "content": answer})
        await update.message.reply_text(answer, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text("⚠️ Brain fog! Try again in a second.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify_click, pattern='verify'))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_ai))
    app.run_polling()