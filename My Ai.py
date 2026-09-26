import requests
import os
import time
from telebot import apihelper
apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 60

import telebot
from google import genai
from PIL import Image

TOKEN = "8588105195:AAF3_W-lOvR8B5YfZ-inAg9nsMMkGqHUEZM"
bot = telebot.TeleBot(TOKEN)

gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# قاموس لحفظ جلسات المحادثة (Chat History) لكل مستخدم لوحده بناءً على الـ ID بتاعه
user_chats = {}

def get_user_chat(user_id):
    if user_id not in user_chats:
        # هنا بنعمل Prompting مبدئي يوجه البوت إنه مساعد ذكي، ودود، وبيجاوب باللغة العربية بوضوح
        system_instruction = (
            "أنت مساعد ذكي وودود جداً، اسمك 'My AI'. مهمتك هي مساعدة الطلاب والمستخدمين "
            "في تلخيص النصوص، شرح الصور بدقة، والإجابة على أي أسئلة بأسلوب منظم وواضح وبدون تعقيد باللغة العربية."
        )
        user_chats[user_id] = gemini_client.chats.create(
            model='gemini-3.6-flash',
            config={
                'system_instruction': system_instruction,
            }
        )
    return user_chats[user_id]

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_text = message.text
    # لما المستخدم يبدأ، بنصفر جلسته عشان تبدأ نضِيفة #
    user_chats.pop(message.chat.id, None)
    bot.reply_to(message, "أهلاً بكِ يا سماء، ومفضل فاكر كل كلامنا سوا، اسألي عليها، وهفضل فاكر كل كلامنا سوا")
    bot.reply_to(message, "جاري التفكير والرد، ثواني...")
    
    chat = get_user_chat(user_id)
    
    max_retries = 3
    response = None
    for attempt in range(max_retries):
        try:
            # استخدام الـ Chat History لإرسال الرسالة مع الاحتفاظ بالسياق
            response = chat.send_message(f"لخص أو أجب على التالي بوضوح وبطريقة مفيدة:\n{user_text}")
            break
        except Exception as e:
            if ("503" in str(e) or "429" in str(e)) and attempt < max_retries - 1:
                time.sleep(5)
                continue
            else:
                raise e

    if response:
        bot.reply_to(message, response.text)

@bot.message_handler(content_types=['photo'])
def handle_image(message):
    try:
        user_id = message.chat.id
        print("تم استلام صورة من المستخدم، جاري معالجتها...")
        bot.reply_to(message, "جاري استقبال الصورة وفهمها، ثواني...")
        
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        image_path = "temp_image.jpg"
        with open(image_path, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        img = Image.open(image_path)
        user_caption = message.caption if message.caption else "اشرح لي ما تحويه هذه الصورة بالتفصيل وأجب على أي سياق مطلوب."

        chat = get_user_chat(user_id)

        max_retries = 3
        response = None
        for attempt in range(max_retries):
            try:
                # إرسال الصورة مع الـ Caption داخل جلسة الشات عشان يفضل فاكرها للأسئلة اللي بعدها
                response = chat.send_message([img, user_caption])
                break
            except Exception as e:
                if ("503" in str(e) or "429" in str(e)) and attempt < max_retries - 1:
                    time.sleep(5)
                    continue
                else:
                    raise e

        bot.reply_to(message, response.text)
        print("تم إرسال شرح ووصف الصورة بنجاح")
        
    except Exception as e:
        print(f"خطأ في معالجة الصورة: {e}")
        bot.reply_to(message, f"عذراً، حدث خطأ أثناء معالجة الصورة أو الرد: {e}")

bot.remove_webhook()
bot.infinity_polling(timeout=60, long_polling_timeout=60)