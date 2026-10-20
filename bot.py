import os
import fitz  # PyMuPDF
from PIL import Image
from telebot import TeleBot
from google import genai

# TELEGRAM BOT TOKENINGIZNI SHU YERGA YOZING


bot = TeleBot(TELEGRAM_TOKEN)
client = genai.Client(api_key=GEMINI_KEY)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Salom! Manga PDF faylini yuboring, uni o'zbek tiliga tarjima qilib beraman.")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if not message.document.file_name.endswith('.pdf'):
        bot.reply_to(message, "Iltimos, faqat PDF formatidagi manga yuboring.")
        return

    msg = bot.reply_to(message, "PDF qabul qilindi. Sahifalar qayta ishlanmoqda...")
    
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    pdf_path = f"temp_{message.chat.id}.pdf"
    with open(pdf_path, 'wb') as new_file:
        new_file.write(downloaded_file)

    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        bot.edit_message_text(f"Jami {total_pages} ta sahifa aniqlandi. Tarjima boshlandi...", chat_id=message.chat.id, message_id=msg.message_id)

        translated_text = ""
        
        for page_num in range(total_pages):
            page = doc[page_num]
            pix = page.get_pixmap(dpi=150)
            img_path = f"page_{message.chat.id}_{page_num}.png"
            pix.save(img_path)

            try:
                image = Image.open(img_path)
                prompt = (
                    "Bu manganing bir sahifasi. Iltimos, rasmdagi barcha dialoglar, "
                    "matnlar va pufakchalardagi yozuvlarni topib, ketma-ketlikda "
                    "ravon o'zbek tiliga tarjima qilib bering."
                )
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[image, prompt]
                )
                
                translated_text += f"\n--- 📄 {page_num + 1}-SAHIFA ---\n\n" + response.text + "\n\n"
                
            except Exception as e:
                translated_text += f"\n--- 📄 {page_num + 1}-SAHIFA ---\nXatolik: {e}\n\n"
            finally:
                if os.path.exists(img_path):
                    os.remove(img_path)

        txt_path = f"Manga_Tarjima_{message.chat.id}.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(translated_text)

        with open(txt_path, "rb") as f:
            bot.send_document(message.chat.id, f, caption="🎉 Tarjima yakunlandi!")

        if os.path.exists(txt_path):
            os.remove(txt_path)

    except Exception as e:
        bot.send_message(message.chat.id, f"Xatolik yuz berdi: {e}")
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

bot.polling(none_stop=True)
