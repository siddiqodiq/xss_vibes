import os
import subprocess
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Token bot Anda
# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('TOKEN')

# Fungsi untuk menjalankan perintah /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! Saya bot XSS Scanner. Gunakan perintah berikut:\n"
        "1. Kirim file .txt berisi URL untuk memulai scan.\n"
        "2. Gunakan perintah /scan dengan sintaks berikut:\n"
        "/scan -u <URL> -o <output> [-t <threads>] [-H <headers>] [--crawl]\n"
        "Contoh:\n"
        "/scan -u http://example.com -o result.txt\n"
        "/scan -f urls.txt -o result.txt -t 5\n"
        "/scan -f urls.txt -H \"Cookies:test=123, User-Agent: Mozilla/Firefox\" -t 7 -o result.txt"
    )

# Fungsi untuk menangani file .txt yang dikirim oleh pengguna
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Dapatkan file yang dikirim
        file = await update.message.document.get_file()
        
        # Simpan file ke direktori lokal
        file_path = f"downloaded_{update.message.document.file_name}"
        await file.download_to_drive(file_path)
        
        # Beri tahu pengguna bahwa file telah diterima
        await update.message.reply_text(f"File {update.message.document.file_name} berhasil diterima. Memulai scan...")
        
        # Jalankan perintah scan menggunakan file yang diterima
        output_file = "scan_result.txt"
        command = ["python3", "main.py", "-f", file_path, "-o", output_file, "-t", "5"]
        result = subprocess.run(command, capture_output=True, text=True)
        
        # Kirim hasil scan ke pengguna
        if result.returncode == 0:
            # Baca hasil scan dari file output
            with open(output_file, "r") as f:
                scan_result = f.read()
            
            # Kirim hasil scan sebagai pesan teks
            await update.message.reply_text(f"Scan selesai!\nHasil:\n{scan_result}")
            
            # Kirim file hasil scan ke pengguna
            with open(output_file, "rb") as f:
                await update.message.reply_document(document=f, filename=output_file)
        else:
            await update.message.reply_text(f"Error:\n{result.stderr}")
        
        # Hapus file setelah selesai diproses
        os.remove(file_path)
        os.remove(output_file)
    except Exception as e:
        await update.message.reply_text(f"Terjadi kesalahan: {str(e)}")

# Fungsi untuk menangani perintah /scan
async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Ambil argumen dari pesan pengguna
        args = update.message.text.split()[1:]
        
        # Jalankan perintah scan menggunakan argumen yang diberikan
        output_file = "scan_result.txt"
        command = ["python3", "main.py"] + args + ["-o", output_file]
        result = subprocess.run(command, capture_output=True, text=True)
        
        # Kirim hasil scan ke pengguna
        if result.returncode == 0:
            # Baca hasil scan dari file output
            with open(output_file, "r") as f:
                scan_result = f.read()
            
            # Kirim hasil scan sebagai pesan teks
            await update.message.reply_text(f"Scan selesai!\nHasil:\n{scan_result}")
            
            # Kirim file hasil scan ke pengguna
            with open(output_file, "rb") as f:
                await update.message.reply_document(document=f, filename=output_file)
        else:
            await update.message.reply_text(f"Error:\n{result.stderr}")
        
        # Hapus file hasil scan setelah dikirim
        os.remove(output_file)
    except Exception as e:
        await update.message.reply_text(f"Terjadi kesalahan: {str(e)}")

# Fungsi utama
def main():
    # Inisialisasi Application dengan token bot
    application = Application.builder().token(TOKEN).build()

    # Daftarkan handler untuk perintah /start
    application.add_handler(CommandHandler("start", start))

    # Daftarkan handler untuk perintah /scan
    application.add_handler(CommandHandler("scan", scan_command))

    # Daftarkan handler untuk file .txt
    application.add_handler(MessageHandler(filters.Document.FileExtension("txt"), handle_file))

    # Mulai bot
    application.run_polling()

if __name__ == '__main__':
    main()