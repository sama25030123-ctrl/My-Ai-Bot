import telebot
from google import genai

# حطي توكن البوت بتاعك هنا
TOKEN = "8588105195:AAFCUIUHDVZoYTpfi-5z5U9GZ2KxV2R8mjY"
bot = telebot.TeleBot(TOKEN)

# إعداد مفتاح وابتكار نموذج جيميناي (تأكدي من وضع مفتاح API الخاص بكِ هنا)
# gemini_client = genai.Client(api_key=" حطي مفتاح Gemini API
# هنا ")
# إعداد مفتاح وابتكار نموذج جيميناي
gemini_client = genai.Client(api_key="AQ.Ab8RN6IJ7b1tdwHeDQx9bCo9DAuV4NT-B0gFGFrHoy1L9tADtg")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً بيكي يا سماء! ابعتي لي أي نص طويل وهلخصهولك فوراً.")

# دالة لاستقبال أي رسالة نصية عادية وتلخيصها
@bot.message_handler(func=lambda message: True)
def summarize_text(message):
    user_text = message.text
    bot.reply_to(message, "جاري تلخيص النص، ثواني...")

    try:
        # هنا بنطلب من جيميناي يلخص النص بطريقة مبسطة ومفيدة
        response = gemini_client.models.generate_content(
            model='gemini-3.6-flash',
            contents=f"لخص النص التالي في نقاط أساسية ومفيدة باللغة العربية:\n{user_text}"
        )
        bot.reply_to(message, response.text)
        
    except Exception as e:
        bot.reply_to(message, f"حدث خطأ أثناء التلخيص: {e}")

bot.remove_webhook()
bot.infinity_polling()