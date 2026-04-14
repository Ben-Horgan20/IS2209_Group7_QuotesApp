from flask import Flask, render_template, request, jsonify
import datetime
import requests
from dotenv import load_dotenv
import os
from supabase import create_client

app = Flask(__name__)
START_TIME = datetime.datetime.utcnow()

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

def check_dependencies():
    checks = {}
    try:
        supabase.table('quotes').select('id').limit(1).execute()
        checks['database'] = 'ok'
    except Exception as e:
        checks['database'] = f'error: {str(e)}'

    checks['external_api'] = 'ok' if API_KEY else 'missing key'
    return checks

@app.route('/health')
def health():
    checks = check_dependencies()
    overall = 'ok' if all(v == 'ok' for v in checks.values()) else 'degraded'
    status_code = 200 if overall == 'ok' else 503
    return jsonify({'status': overall, 'checks': checks}), status_code

@app.route('/status')
def status():
    checks = check_dependencies()
    overall = 'ok' if all(v == 'ok' for v in checks.values()) else 'degraded'
    uptime = datetime.datetime.utcnow() - START_TIME
    quote_count = None
    try:
        result = supabase.table('quotes').select('id', count='exact').execute()
        quote_count = result.count
    except Exception:
        pass
    return render_template('status.html',
        overall=overall,
        checks=checks,
        uptime=str(uptime).split('.')[0],
        quote_count=quote_count
    )

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
    categories = 'wisdom,success,humor'
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
