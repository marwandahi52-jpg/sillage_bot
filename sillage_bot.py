import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ==========================================
# 1. إعدادات النظام وقاعدة البيانات 🗄️
# ==========================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = "9294117411:AAGOhGPGX_MNrIbcMzrSEVAFs3Z8-T29uMQ"
ADMIN_PHONE = "0981155067"  # رقم الدعم الخاص بك
ADMIN_CHAT_ID = "8342986399"  # معرف حسابك لاستقبال الإشعارات البرمجية


def init_db():
    """إنشاء قاعدة البيانات لتخزين الطلبات بدقة وحفظ اسم العميل"""
    conn = sqlite3.connect('ghirn_perfumes.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            customer_name TEXT,
            perfume_name TEXT,
            city TEXT,
            address TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()
    
# ==========================================
# 2. واجهة المستخدم وأزرار القوائم 📱
# ==========================================

async def post_init(application):
    """تهيئة أوامر البوت بالطريقة الاحترافية السليمة عند الإقلاع"""
    await application.bot.set_my_commands([
        BotCommand("start", "البدء من جديد وعرض العطور 🧴")
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دالة الترحيب وعرض قائمة العطور بالليرة السورية"""
    user_name = update.effective_user.first_name
    
    # مسح أي بيانات مؤقتة سابقة عند إعادة البدء
    context.user_data.clear()
    
    keyboard = [
        [InlineKeyboardButton("💎 عطر غيرن الملكي (Ghirn Royal) - 450,000 ل.س", callback_data='perfume_royal')],
        [InlineKeyboardButton("✨ عطر سِيلاج الفاخر (Sillage) - 380,000 ل.س", callback_data='perfume_sillage')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f'أهلاً بك يا {user_name} في بوت عطور "غيرن" 🧴✨.\n\n'
        f'نحن نقدم توصيلاً متاحاً لجميع المحافظات السورية. اختر العطر المناسب للبدء:',
        reply_markup=reply_markup
    )


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع تفاعرات الأزرار، العطور، المحافظات، وزر الرجوع"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # زر الرجوع للقائمة الرئيسية (مع حذف رسالة الصورة لتجنب أخطاء التيليجرام)
    if data == 'back_to_start':
        context.user_data.clear()
        keyboard = [
            [InlineKeyboardButton("💎 عطر غيرن الملكي (Ghirn Royal) - 450,000 ل.س", callback_data='perfume_royal')],
            [InlineKeyboardButton("✨ عطر سِيلاج الفاخر (Sillage) - 380,000 ل.س", callback_data='perfume_sillage')]
        ]
        
        try:
            await query.message.delete()
        except Exception:
            pass
            
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text='أهلاً بك مجدداً في بوت عطور "غيرن" 🧴✨.\n\n'
                 'اختر العطر المناسب للبدء:',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # اختيار عطر غيرن الملكي وعرض صورته
    if data == 'perfume_royal':
        context.user_data['pending_perfume'] = "عطر غيرن الملكي"
        keyboard = [
            [InlineKeyboardButton("🚚 متابعة لاختيار المحافظة", callback_data='to_cities')],
            [InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data='back_to_start')]
        ]
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo="https://images.unsplash.com/photo-1523293182086-7651a899d37f", 
            caption="💎 **عطر غيرن الملكي (Ghirn Royal)**\n\nمزيج ساحر من العود الفاخر والمسك الأبيض.\n💰 السعر: 450,000 ل.س",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    # اختيار عطر سِيلاج وعرض صورته
    elif data == 'perfume_sillage':
        context.user_data['pending_perfume'] = "عطر سِيلاج"
        keyboard = [
            [InlineKeyboardButton("🚚 متابعة لاختيار المحافظة", callback_data='to_cities')],
            [InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data='back_to_start')]
        ]
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo="https://images.unsplash.com/photo-1592945403244-b3fbafd7f539",
            caption="✨ **عطر سِيلاج الفاخر (Sillage)**\n\nنفحات منعشة من اللافندر والبرغموت مع قاعدة دافئة من الفانيليا.\n💰 السعر: 380,000 ل.س",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    elif data == 'to_cities':
        await show_cities_menu(query, is_edit=False)
        
    # اختيار المحافظة وتحديد خطوة طلب الاسم
    elif data.startswith('city_'):
        city_name = data.replace('city_', '').replace('_', ' ')
        context.user_data['pending_city'] = city_name
        context.user_data['step'] = 'awaiting_name'
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data='back_to_start')]]
        
        await query.message.reply_text(
            text=f"📍 لقد اخترت محافظة: **{city_name}**\n\n"
                 f"📝 يرجى الآن إرسال **اسمك الثلاثي** لكي يتم تسجيله في الطلب:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def show_cities_menu(query, is_edit=False):
    """عرض قائمة المحافظات المتاحة للتوصيل مع زر رجوع"""
    keyboard = [
        [InlineKeyboardButton("دمشق", callback_data='city_دمشق'), InlineKeyboardButton("ريف دمشق", callback_data='city_ريف_دمشق')],
        [InlineKeyboardButton("حلب", callback_data='city_حلب'), InlineKeyboardButton("حمص", callback_data='city_حمص')],
        [InlineKeyboardButton("اللاذقية", callback_data='city_اللاذقية'), InlineKeyboardButton("طرطوس", callback_data='city_طرطوس')],
        [InlineKeyboardButton("حماة", callback_data='city_حماة'), InlineKeyboardButton("درعا", callback_data='city_درعا')],
        [InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data='back_to_start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "🚚 **خدمة التوصيل متاحة لجميع المحافظات السورية**\n\n"
        "الرجاء اختيار المحافظة المستهدفة من القائمة أدناه:"
    )
    
    if is_edit:
        await query.edit_message_text(text=text, reply_markup=reply_markup)
    else:
        await query.message.reply_text(text=text, reply_markup=reply_markup)    
# ==========================================
# 3. معالجة نصوص رسائل العملاء (الاسم والعنوان) 📦
# ==========================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إدارة خطوات إدخال البيانات وحفظ الطلب وإرسال تنبيه للمشرف دون تعليق"""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    step = context.user_data.get('step')
    
    # الخطوة أ: استلام اسم العميل والانتقال لطلب العنوان
    if step == 'awaiting_name':
        context.user_data['customer_name'] = user_message
        context.user_data['step'] = 'awaiting_address'
        
        await update.message.reply_text(
            f"👤 تم تسجيل الاسم: **{user_message}**\n\n"
            f"📍 يرجى الآن إرسال **عنوانك بالتفصيل (المنطقة، الشارع، ورقم الهاتف)** لإتمام الطلب:"
        )
        return

    # الخطوة ب: استلام العنوان وإتمام الطلب وحفظه في قاعدة البيانات
    if step == 'awaiting_address':
        customer_name = context.user_data.get('customer_name', 'غير متوفر')
        perfume_name = context.user_data.get('pending_perfume', 'عطر غير محدد')
        city = context.user_data.get('pending_city', 'غير محددة')
        address = user_message
        
        # حفظ البيانات في قاعدة البيانات
        try:
            conn = sqlite3.connect('ghirn_perfumes.db')
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO orders (user_id, customer_name, perfume_name, city, address, status) VALUES (?, ?, ?, ?, ?, ?)',
                (user_id, customer_name, perfume_name, city, address, 'قيد المعالجة')
            )
            conn.commit()
            conn.close()
        except Exception as db_err:
            print(f"خطأ في قاعدة البيانات: {db_err}")

        # مسح البيانات المؤقتة لتنظيف الذاكرة وتجنب التكرار
        context.user_data.clear()
        
        # رد تأكيد للعميل مع زر للبدء من جديد
        keyboard = [[InlineKeyboardButton("🛍️ طلب عطر آخر (/start)", callback_data='back_to_start')]]
        await update.message.reply_text(
            f"✅ **تم تأكيد طلبك بنجاح!**\n\n"
            f"👤 الاسم: {customer_name}\n"
            f"📦 المنتج: {perfume_name}\n"
            f"🏙️ المحافظة: {city}\n"
            f"📍 العنوان: {address}\n\n"
            f"شكراً لتسوقك معنا في عطور غيرن. سنقوم بالتواصل معك قريباً.\n"
            f"📞 للدعم المباشر والاتصال: {ADMIN_PHONE}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # إرسال إشعار فوري إلى حسابك الشخصي (المشرف)
        if ADMIN_CHAT_ID:
            admin_notification = (
                f"🚨 **طلب جديد تم استلامه!** 📦\n\n"
                f"👤 اسم العميل: **{customer_name}**\n"
                f"🆔 معرف المستخدم: `{user_id}`\n"
                f"💎 المنتج المطلوب: {perfume_name}\n"
                f"🏙️ المحافظة: {city}\n"
                f"📍 العنوان ورقم الهاتف: {address}"
            )
            try:
                await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_notification, parse_mode="Markdown")
            except Exception as e:
                print(f"فشل إرسال الإشعار للمشرف: {e}")
    else:
        await update.message.reply_text(
            f"أهلاً بك! يرجى استخدام الأمر /start لبدء تصفح العطور.\n"
            f"📞 للتواصل المباشر مع الدعم: {ADMIN_PHONE}"
        )


# ==========================================
# 4. تشغيل البوت 🚀
# ==========================================

if __name__ == '__main__':
    init_db()
    
    # بناء التطبيق مع حقن post_init لتنفيذ التهيئة البرمجية بأمان
    application = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("البوت الاحترافي لعطور غيرن يعمل الآن بطلب الاسم والعنوان بدقة وبدون أخطاء... 🚀")
    application.run_polling()    