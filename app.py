from flask import Flask, render_template, request
import requests
from dotenv import load_dotenv
import os
from supabase import create_client

app = Flask(__name__)

load_dotenv()

API_KEY = os.getenv("NAME_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
def save_quote(quote, author, work, category, source):
    supabase.table('quotes').insert({
        "quote": quote,
        "author": author,
        "work": work,
        "category": category,
        "source": source,
    }).execute()

@app.route('/')
def index():

    # Quote of the Day
    qotd_response = requests.get(
        'https://api.api-ninjas.com/v2/quoteoftheday',
        headers={"X-Api-Key": API_KEY}
    )
    data = qotd_response.json()[0]
    qotd_quote = data['quote']
    qotd_author = data['author']
    qotd_work = data['work']
    save_quote(qotd_quote, qotd_author, qotd_work, None, 'qotd')

    # Random quotes
    rand_response = requests.get(
        'https://api.api-ninjas.com/v2/randomquotes',
        headers={"X-Api-Key": API_KEY}
    )
    data = rand_response.json()[0]
    rand_quote = data['quote']
    rand_author = data['author']
    rand_work = data['work']
    save_quote(rand_quote, rand_author, rand_work, None, 'random')

    # Generic quotes
    categories = 'success,wisdom'
    response = requests.get(
        'https://api.api-ninjas.com/v2/randomquotes',
        headers={"X-Api-Key": API_KEY},
        params={'categories': categories}
    )
    data = response.json()[0]
    quote = data['quote']
    author = data['author']
    work = data['work']
    save_quote(quote, author, work, categories, 'category')

    recent_quotes = supabase.table('quotes').select('*').order('fetched_at', desc=True).limit(5).execute().data


    return render_template('index.html', qotd_quote=qotd_quote, qotd_author=qotd_author, qotd_work=qotd_work,
                           rand_quote=rand_quote, rand_author=rand_author, rand_work=rand_work,
                           quote=quote, author=author, work=work, recent_quotes=recent_quotes)




if __name__ == '__main__':
    app.run(debug=True)
