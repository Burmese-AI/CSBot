from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
import os
import requests
import json 

load_dotenv()
apiKey = os.getenv("BOT_ACCESS")
third_partyAPI = os.getenv("INFORMATION")
news_api_url = os.getenv("NEWS_API")

with open('algorithms.json', 'r') as file:
    ALGORITHMS = json.load(file)

with open('books.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

BOOKS = data["books"]


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usage = (
        "hello - Greet the bot\n"
        "resources - Get a list of useful Computer Science resources\n"
        "latestNew - read the latest tech News"
        "/explore <topic> - Get a brief explanation and related links from Wikipedia\n"
        "/algorithm <name> - Get a brief explanation and related links from Programiz\n"
        "/books <category> - Get the Book Recommendation based on category "
    )
    await update.message.reply_text(f'Welcome! You can ask anything related to Computer Science and other topics.\n{usage}')

async def resources(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    resources_message = (
        "Here are some useful resources for Computer Science students:\n\n"
        "1. [GeeksforGeeks](https://www.geeksforgeeks.org/)\n"
        "2. [Programiz](https://www.programiz.com/)\n"
    )
    await update.message.reply_text(resources_message, parse_mode='Markdown')

async def explore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please specify the topic to explore. \n e.g., /explore OOP")
        return

    topic = ' '.join(context.args)
    explanation, links = await fetch_from_wikipedia(topic)

    if not explanation:
        await update.message.reply_text(f"Sorry, I couldn't find information about '{topic}' on Wikipedia.")
        return

    links_text = "\n\nHere are some related links:\n" + "\n".join([f"- [{link}](https://en.wikipedia.org/wiki/{link.replace(' ', '_')})" for link in links]) if links else ""

    await update.message.reply_text(explanation + links_text, parse_mode='Markdown')

async def algorithm_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) == 0:
        await update.message.reply_text("Please specify the algorithm name.\n e.g. /algorithm bubblesort")
        return

    algorithm_name = context.args[0].lower()

    if algorithm_name in ALGORITHMS:
        description = ALGORITHMS[algorithm_name]["description"]
        link = ALGORITHMS[algorithm_name]["link"]
        response = f"Algorithm: {algorithm_name.capitalize()}\n\nDescription: {description}\n\nLearn more: {link}"
    else:
        response = "Algorithm not found. Please specify a valid algorithm name."

    await update.message.reply_text(response)

async def fetch_from_wikipedia(page_title, max_length=800):
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts|links",
        "titles": page_title,
        "explaintext": True  
    }
    try:
        response = requests.get(third_partyAPI, params=params)
        response.raise_for_status()
        data = response.json()

        page_id = next(iter(data['query']['pages']))
        page_info = data['query']['pages'][page_id]

        extract = page_info.get('extract', '')
        if len(extract) > max_length:
            extract = extract[:max_length] + '...'

        links = [link['title'] for link in page_info.get('links', [])]

        return extract.strip(), links
    except (requests.RequestException, KeyError) as e:
        print(f"Error fetching from Wikipedia: {e}")
        return None, []
    
    text = update.message.text.lower()


async def book_recommendation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) == 0:
        await update.message.reply_text("Please specify the book category.\n e.g. /books programming")
        return

    category = context.args[0].lower()
    matching_books = [book for book in BOOKS if book["category"] == category]

    if matching_books:
        response = "\n\n".join([
            f"Title: {book['title']}\n\n Author: {book['author']}\nDescription: {book['description']}"
            for book in matching_books
        ])
    else:
        response = "No books found in this category. Please specify a valid category."

    await update.message.reply_text(response)

async def latestNews(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    new_api_response = requests.get(news_api_url).json()
    articles = new_api_response.get('articles', [])
    
    if not articles:
        await update.message.reply_text("Sorry for inconvinence. I could not able to fetch the latest News")
        return 
    
    news_message = "Here is the latest news for technology: \n"
    for article in articles[:5]:
        
        title = article['title']
        url = article['url']
        news_message += f" -**[{title}]({url})**\n\n"
   
    await update.message.reply_text(news_message, parse_mode='Markdown')



async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if "hello" in text or "hi" in text:
        await hello(update, context)
    elif "start" in text:
        await start(update, context)
    elif "resources" in text:
        await resources(update, context)
    elif "latestnews" in text:
        await latestNews(update, context)
    elif "algorithm" in text:
        await algorithm_list(update, context)
    elif text.startswith("explore"):
        topic = text.replace("explore", '').strip()
        if topic:
            await explore(update, context)
        else:
            await update.message.reply_text("Please specify the topic that you want to explore.")
    else:
        await update.message.reply_text("Sorry, I couldn't understand what you are asking about. Type /start to see available commands.")     

    
def main() -> None:
    app = ApplicationBuilder().token(apiKey).build()
    app.add_handler(CommandHandler("hello", hello))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("resources", resources))
    app.add_handler(CommandHandler("explore", explore))
    app.add_handler(CommandHandler("latestNews",latestNews))
    app.add_handler(CommandHandler("algorithm",algorithm_list))
    app.add_handler(CommandHandler("books",book_recommendation))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
