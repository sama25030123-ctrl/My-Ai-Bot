import telebot

TOKEN = "8614408893:AAEYT-C5ciTpH4FRRBTrvxec1xs05MgCLXQ"
bot = telebot.TeleBot(TOKEN)

users_file = "users_list.txt"

@bot.message_handler(func=lambda message: True)
def track_and_reply(message):
    user_id = str(message.from_user.id)
    # بناخد الاسم الأول واسم العائلة لو كاتبهم في بروفايل تيليجرام
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()
    
    # لو مفيش اسم، بنكتب "مجهول" بدل No Username
    if not full_name:
        full_name = "بدون اسم"
    
    try:
        with open(users_file, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        content = ""
        
    # بنسجل المستخدم لو الـ ID مش موجود قبل كده في الملف
    if user_id not in content:
        with open(users_file, "a", encoding="utf-8") as f:
            f.write(f"ID: {user_id} - Name: {full_name}\n")
            
    bot.reply_to(message, "أهلاً بيك! تم تسجيل حضورك بنجاح 🚀")

print("البوت التجريبي يعمل الآن...")
bot.infinity_polling()