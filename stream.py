import os
import time
import tweepy
from tweepy.errors import TooManyRequests
from langchain_openai import OpenAIEmbeddings, OpenAI
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

TRACK_KEYWORD = "Bu Bir Denemedir."

# Vektör deposu ayarı
os.makedirs("vectorstore", exist_ok=True)

embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
chroma = Chroma("adalet_tweets", embedding_function=embeddings, persist_directory="vectorstore")
llm = OpenAI(model="gpt-4o", temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY"))

def fetch_and_process_tweets():
    """
    Twitter'dan tweet çeker ve vektör veritabanına işler.
    """
    client = tweepy.Client(bearer_token= os.getenv("TWITTER_BEARER_TOKEN"))
    print(f"'{TRACK_KEYWORD}' kelimesiyle tweetler aranıyor...")

    try:
        response = client.search_recent_tweets(
            query=TRACK_KEYWORD,
            max_results=10,
            tweet_fields=["text"]
        )
    except TooManyRequests:
        print("Rate limit aşıldı. 15 dakika bekleniyor...")
        time.sleep(15 * 60)
        return
    except Exception as e:
        print(f"Hata oluştu: {e}")
        return

    if not response.data:
        print("Hiç tweet bulunamadı.")
        return

    for tweet in response.data:
        text = tweet.text.strip()
        print(f"Tweet: {text[:100]}...")

        chroma.add_texts([text])
        chroma.persist()

        prompt = f"Bu tweeti eğer Türkçe değilse türkçeye çevir. Ardından kısaca özetle:\n\n{text}"
        summary = llm(prompt)
        print("Çeviri/Özet:", summary)
        print("-" * 50)


# Eğer bu dosya doğrudan çalıştırılırsa sadece tweet botu başlasın
if __name__ == "__main__":
    while True:
        fetch_and_process_tweets()
        print("5 dakika bekleniyor...\n")
        time.sleep(5 * 60)
