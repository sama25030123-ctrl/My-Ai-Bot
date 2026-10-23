import streamlit as st
import telebot
from google import genai
import threading
import os

# --- 1. إعداد العناوين والمفاتيح ---
TOKEN = "8986693714:AAGkyZCvIsaUxT0FfGq7WkJYw8pHi_gz-8A"
API_KEY = os.environ.get("GEMINI_API_KEY", "ضع_المفتاح_هنا_في_حال_عدم_وجود_متغير")

bot = telebot.TeleBot(TOKEN)
gemini_client = genai.Client(api_key=API_KEY)
users_file = "users_list.txt"

# --- 2. دالة تسجل المستخدمين ---
def save_user_if_new(user):
    user_id = str(user.id)
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    full_name = f"{first_name} {last_name}".strip() or "بدون اسم"
    
    try:
        with open(users_file, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        content = ""
        
    if user_id not in content:
        with open(users_file, "a", encoding="utf-8") as f:
            f.write(f"ID: {user_id} - Name: {full_name}\n")

# --- 3. معالجة رسائل البوت (الذكاء الاصطناعي والشات) ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_user_if_new(message.from_user)
    bot.reply_to(message, "أهلاً بيكي! أنا مساعدكِ الذكي جاهز لأي سؤال أو تلخيص.")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    save_user_if_new(message.from_user)
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=message.text
        )
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"حدث خطأ: {e}")

# --- 4. تشغيل البوت في الخلفية لملاءمة Streamlit ---
def run_bot():
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)

# تشغيل الثريد ليبقى البوت مستمراً
if "bot_started" not in st.session_state:
    st.session_state["bot_started"] = True
    threading.Thread(target=run_bot, daemon=True).start()

# --- 5. واجهة Streamlit Dashboard ---
st.title("🤖 Telegram AI Bot Dashboard")
st.success("البوت يعمل الآن بنجاح ومتصل بـ Telegram!")

st.subheader("📋 قائمة المستخدمين المسجلين:")
if os.path.exists(users_file):
    with open(users_file, "r", encoding="utf-8") as f:
        st.text(f.read())
else:
    st.info("لا يوجد مستخدمين مسجلين حتى الآن.")