import os
import subprocess
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('TOKEN')

# Fungsi untuk menjalankan perintah /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! Saya bot XSS Scanner. Gunakan perintah berikut:\n"
        "1. Kirim file .txt berisi URL untuk memulai scan.\n"
        "2. Gunakan perintah /scan dengan sintaks berikut:\n"
        "/scan -u <URL> -o <output> [-t <threads>] [-H <headers>] [--crawl] [--waf] [-w <waf_name>]\n"
        "Contoh:\n"
        "/scan -u http://example.com -o result.txt\n"
        "/scan -u http://example.com -o result.txt --waf\n"
        "/scan -u http://example.com -o result.txt -w cloudflare\n"
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
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                # Baca hasil scan dari file output
                with open(output_file, "r") as f:
                    scan_result = f.read()
                
                # Kirim hasil scan sebagai pesan teks
                await update.message.reply_text(f"Scan selesai!\nHasil:\n{scan_result}")
                
                # Kirim file hasil scan ke pengguna
                with open(output_file, "rb") as f:
                    await update.message.reply_document(document=f, filename=output_file)
            else:
                await update.message.reply_text("Scan selesai, tetapi tidak ada kerentanan yang ditemukan.")
        else:
            await update.message.reply_text(f"Error:\n{result.stderr}")
        
        # Hapus file setelah selesai diproses
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(output_file):
            os.remove(output_file)
    except Exception as e:
        await update.message.reply_text(f"Terjadi kesalahan: {str(e)}")

# Fungsi untuk menangani perintah /scan
async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Ambil argumen dari pesan pengguna
        args = update.message.text.split()[1:]
        
        # Periksa apakah ada argumen --waf atau -w
        if "--waf" in args:
            # Jika --waf digunakan, tambahkan ke perintah
            args.append("--waf")
        elif "-w" in args:
            # Jika -w digunakan, pastikan ada nilai WAF yang diberikan
            waf_index = args.index("-w")
            if waf_index + 1 < len(args):
                waf_name = args[waf_index + 1]
                args.extend(["-w", waf_name])
            else:
                await update.message.reply_text("Error: Nama WAF tidak diberikan setelah -w.")
                return
        
        # Jalankan perintah scan menggunakan argumen yang diberikan
        output_file = "scan_result.txt"
        command = ["python3", "main.py"] + args + ["-o", output_file]
        result = subprocess.run(command, capture_output=True, text=True)
        
        # Kirim hasil scan ke pengguna
        if result.returncode == 0:
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                # Baca hasil scan dari file output
                with open(output_file, "r") as f:
                    scan_result = f.read()
                
                # Kirim hasil scan sebagai pesan teks
                await update.message.reply_text(f"Scan selesai!\nHasil:\n{scan_result}")
                
                # Kirim file hasil scan ke pengguna
                with open(output_file, "rb") as f:
                    await update.message.reply_document(document=f, filename=output_file)
            else:
                await update.message.reply_text("Scan selesai, tetapi tidak ada kerentanan yang ditemukan.")
        else:
            await update.message.reply_text(f"Error:\n{result.stderr}")
        
        # Hapus file hasil scan setelah dikirim
        if os.path.exists(output_file):
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