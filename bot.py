import logging
import asyncio
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات وبياناتك الشخصية ---
BOT_TOKEN = "8113895476:AAFs7z3vBLklVsvjkb2n7JJrHLYR-54reWQ"
OWNER_ID = 6897059058
OWNER_USERNAME = "@AksarChef"
CHANNEL_USERNAME = "@qaevnn"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# دالة برمجية للاتصال بسيرفر الواتساب المحلي وجلب الكود الحقيقي
def fetch_whatsapp_code(phone_number):
    try:
        url = "http://localhost:3000/get-pairing-code" 
        response = requests.post(url, json={"phone": phone_number}, timeout=20)
        if response.status_code == 200:
            data = response.json()
            return data.get("code")
        return None
    except Exception as e:
        print(f"Error fetching code: {e}")
        return None

# دالة التحقق من الاشتراك واستثناء المالك
async def check_subscription(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

# أمر البداية /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_subscription(context, user_id):
        keyboard = [
            [InlineKeyboardButton("📢 اشترك في القناة أولاً", url="https://t.me/qaevnn")],
            [InlineKeyboardButton("✅ تم الاشتراك، اضغط للتأكيد", callback_data="check_sub")]
        ]
        await update.message.reply_text(
            "⚠️ عذراً يا صديقي! يجب عليك الاشتراك في قناة البوت أولاً للوصول إلى اللوحة.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await show_main_menu(update, context)

# عرض لوحة التحكم الرئيسية
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👑 *مرحباً بك في لوحة تحكم المساعد السري للواتساب!*\n\n"
        "**المميزات النشطة عند الربط:**\n"
        "🔄 كشف ومراقبة الرسائل المعدلة فوراً.\n"
        "🗑️ منع حذف الرسائل وتخزينها لحمايتك.\n"
        "🔓 فك قفل صور وفيديوهات (العرض لمرة واحدة).\n\n"
        "الرجاء الضغط على الزر بالأسفل لربط رقم واتساب الخاص بك."
    )
    keyboard = [
        [InlineKeyboardButton("📱 ربط رقم الواتساب بالبوت", callback_data="connect_whatsapp")],
        [InlineKeyboardButton("👨‍💻 مراسلة المالك", url="https://t.me/AksarChef")]
    ]
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# معالجة الأزرار
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "check_sub":
        if await check_subscription(context, query.from_user.id):
            await show_main_menu(update, context)
        else:
            await query.message.reply_text("❌ لم تشترك بعد!")
    elif query.data == "connect_whatsapp":
        await query.message.reply_text("📞 أرسل رقم هاتف الواتساب الخاص بك مع رمز الدولة (مثال: +967781196215):")
        context.user_data['waiting_for_phone'] = True

# استقبال البيانات والربط الفعلي المطور
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    if context.user_data.get('waiting_for_phone'):
        phone_clean = user_text.strip().replace(" ", "").replace("-", "")
        context.user_data['phone_number'] = phone_clean
        context.user_data['waiting_for_phone'] = False
        
        # رسالة جاري جلب الكود الفعلي من السيرفر
        loading_msg = await update.message.reply_text(
            f"📥 *جاري الاتصال بخوادم الواتساب وطلب كود ربط رسمي للرقم:* `{phone_clean}`...\n🔄 يرجى الانتظار ثوانٍ لتوليد الكود الحقيقي.",
            parse_mode="Markdown"
        )
        
        # استدعاء السيرفر لجلب الكود الحقيقي
        pairing_code = fetch_whatsapp_code(phone_clean)
        
        if pairing_code:
            # تنسيق الكود بالشكل المعتاد للواتساب (AAAA-BBBB) ليصبح سهلاً
            formatted_code = f"{pairing_code[:4]}-{pairing_code[4:]}" if len(pairing_code) == 8 else pairing_code
            
            await loading_msg.edit_text(
                f"🔑 *تم توليد كود الربط الرسمي بنجاح!*\n\n"
                f"كود ربط الأجهزة الخاص بك هو:\n"
                f"📎 `{formatted_code}`\n\n"
                "💡 **طريقة التفعيل:**\n"
                "1️⃣ افتح تطبيق الواتساب في هاتفك.\n"
                "2️⃣ اذهب إلى الإعدادات -> الأجهزة المرتبطة -> ربط جهاز.\n"
                "3️⃣ اختر 'الربط برقم الهاتف بدلاً من ذلك'.\n"
                f"4️⃣ أدخل الكود الموضح أعلاه `{formatted_code}` ليتم الربط التام!",
                parse_mode="Markdown"
            )
        else:
            await loading_msg.edit_text(
                "❌ *فشل الاتصال بسيرفر الواتساب أو أن الرقم غير صحيح!*\n"
                "تأكد من كتابة الرقم بشكل صحيح مع رمز الدولة، أو أن سيرفر Node.js لا يعمل في الخلفية.",
                parse_mode="Markdown"
            )

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    print("⚡ البوت الحقيقي جاهز ومربوط بسيرفر الواتساب...")
    application.run_polling()

if __name__ == '__main__':
    main()


