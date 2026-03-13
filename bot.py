import requests
import json
import os
import datetime
import feedparser

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering


TOKEN =  "8615688775:AAGJRiEBtd36DHCqcjjI7i-BE0JOPjU-6C8"
CHAT_ID = 6057210461

NOT_DOSYA = "notlar.json"


RSS_LIST = [
"https://feeds.bbci.co.uk/turkce/rss.xml",
"https://www.cnnturk.com/feed/rss/all/news",
"https://www.ntv.com.tr/son-dakika.rss",
"https://www.haberturk.com/rss",
"https://www.trthaber.com/manset_articles.rss"
]


model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


if not os.path.exists(NOT_DOSYA):
    with open(NOT_DOSYA, "w") as f:
        json.dump([], f)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    mesaj = (
        "Merhaba Cemal 👋\n\n"
        "Komutlar:\n"
        "/piyasa\n"
        "/not\n"
        "/notlar\n"
        "/not_sil\n"
        "/gundem"
    )

    await update.message.reply_text(mesaj)


async def piyasa(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        url = "https://api.coingecko.com/api/v3/simple/price"

        params = {
            "ids": "bitcoin,ethereum",
            "vs_currencies": "usd"
        }

        r = requests.get(url, params=params)
        data = r.json()

        btc = data["bitcoin"]["usd"]
        eth = data["ethereum"]["usd"]

        mesaj = f"📈 Piyasa\n\nBTC: ${btc}\nETH: ${eth}"

    except:

        mesaj = "Piyasa verisi alınamadı."

    await update.message.reply_text(mesaj)


async def not_ekle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("Not yaz.")
        return

    yeni_not = " ".join(context.args)

    with open(NOT_DOSYA, "r") as f:
        notlar = json.load(f)

    notlar.append(yeni_not)

    with open(NOT_DOSYA, "w") as f:
        json.dump(notlar, f)

    await update.message.reply_text("Not kaydedildi.")


async def notlar(update: Update, context: ContextTypes.DEFAULT_TYPE):

    with open(NOT_DOSYA, "r") as f:
        notlar = json.load(f)

    if not notlar:
        await update.message.reply_text("Henüz not yok.")
        return

    mesaj = "Notların\n\n"

    for i, n in enumerate(notlar, 1):

        mesaj += f"{i}. {n}\n"

    await update.message.reply_text(mesaj)


async def not_sil(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("Numara yaz.")
        return

    try:

        index = int(context.args[0]) - 1

        with open(NOT_DOSYA, "r") as f:
            notlar = json.load(f)

        silinen = notlar.pop(index)

        with open(NOT_DOSYA, "w") as f:
            json.dump(notlar, f)

        await update.message.reply_text(f"Silindi: {silinen}")

    except:

        await update.message.reply_text("Hata.")


def haberleri_getir():

    basliklar = []

    for url in RSS_LIST:

        feed = feedparser.parse(url)

        for entry in feed.entries[:10]:

            basliklar.append(entry.title)

    return basliklar


def ortak_haberleri_bul():

    basliklar = haberleri_getir()

    embeddings = model.encode(basliklar)

    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=1.2
    )

    labels = clustering.fit_predict(embeddings)

    clusters = {}

    for i, label in enumerate(labels):

        if label not in clusters:
            clusters[label] = []

        clusters[label].append(basliklar[i])

    sonuc = []

    for cluster in clusters.values():

        sonuc.append(cluster[0])

    return sonuc[:5]


async def gundem(update: Update, context: ContextTypes.DEFAULT_TYPE):

    haberler = ortak_haberleri_bul()

    mesaj = "🧠 Türkiye Gündemi\n\n"

    for i, h in enumerate(haberler, 1):

        mesaj += f"{i}️⃣ {h}\n"

    await update.message.reply_text(mesaj)


async def gunluk_rapor(context: ContextTypes.DEFAULT_TYPE):

    try:

        url = "https://api.coingecko.com/api/v3/simple/price"

        params = {
            "ids": "bitcoin,ethereum",
            "vs_currencies": "usd"
        }

        r = requests.get(url, params=params)
        data = r.json()

        btc = data["bitcoin"]["usd"]

        haberler = ortak_haberleri_bul()

        mesaj = f"📊 Cemal Günlük Rapor\n\nBTC: ${btc}\n\n"

        for i, h in enumerate(haberler[:3], 1):

            mesaj += f"{i}. {h}\n"

    except:

        mesaj = "Rapor oluşturulamadı."

    await context.bot.send_message(chat_id=CHAT_ID, text=mesaj)


def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("piyasa", piyasa))
    app.add_handler(CommandHandler("not", not_ekle))
    app.add_handler(CommandHandler("notlar", notlar))
    app.add_handler(CommandHandler("not_sil", not_sil))
    app.add_handler(CommandHandler("gundem", gundem))

    job_queue = app.job_queue

    job_queue.run_daily(
        gunluk_rapor,
        time=datetime.time(hour=9, minute=0)
    )

    print("Bot çalışıyor...")

    app.run_polling()


if __name__ == "__main__":
    main()