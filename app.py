import sqlite3
import os 
from functools import wraps
from datetime import datetime
from flask import (
    Flask, request, redirect, url_for,
    render_template_string, flash, session, abort
)

app = Flask(__name__)
app.secret_key = os.environ.get(
    "NEWS_SECRET_KEY", "change-this-secret-key"
)

DB_NAME = "news.db"
ADMIN_USER = os.environ.get("NEWS_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("NEWS_ADMIN_PASSWORD", "admin123")

CATEGORIES = [
    "জাতীয়", "রাজনীতি", "আন্তর্জাতিক", "খেলাধুলা",
    "বিনোদন", "প্রযুক্তি", "অর্থনীতি"
]

# ---------------- DATABASE ----------------

def get_db():
    db = sqlite3.connect(DB_NAME)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                summary TEXT NOT NULL,
                content TEXT NOT NULL,
                image TEXT DEFAULT '',
                author TEXT DEFAULT 'News Desk',
                featured INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)

        count = db.execute(
            "SELECT COUNT(*) FROM news"
        ).fetchone()[0]

        if count == 0:
            demo_news = [
                (
                    "স্মার্ট বাংলাদেশ গঠনে এআই এবং ক্লাউড প্রযুক্তির গুরুত্ব অপরিসীম",
                    "প্রযুক্তি",
                    "তথ্যপ্রযুক্তির আধুনিক যুগে তরুণ প্রজন্মকে কৃত্রিম বুদ্ধিমত্তা ও ক্লাউড কম্পিউটিংয়ে দক্ষ করে তোলার ওপর বিশেষ জোর দিচ্ছেন বিশেষজ্ঞরা।",
                    "তথ্যপ্রযুক্তির দ্রুত প্রসারের সাথে সাথে বাংলাদেশও এখন চতুর্থ শিল্পবিপ্লবের পথে এগিয়ে চলেছে। দেশের তরুণ সমাজ সফটওয়্যার উন্নয়ন, কৃত্রিম বুদ্ধিমত্তা (AI) এবং ক্লাউড কম্পিউটিংয়ের মতো নিত্যনতুন প্রযুক্তি আয়ত্ত করে দেশের সীমানা ছাড়িয়ে বৈশ্বিক বাজারে ভূমিকা রাখছে। বিশেষ করে ফ্রিল্যান্সিং এবং স্টার্টআপ সংস্কৃতির প্রসারে দেশের প্রযুক্তি খাতের চেহারা পাল্টে গেছে। বিশেষজ্ঞরা মনে করছেন, যথাযথ প্রশিক্ষণ এবং আধুনিক ল্যাব সুবিধা নিশ্চিত করা গেলে বাংলাদেশ অচিরেই দক্ষিণ এশিয়ার অন্যতম প্রধান প্রযুক্তি হাবে পরিণত হবে।",
                    "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80",
                    "টেক ডেস্ক", 1
                ),
                (
                    "আসন্ন টি-টোয়েন্টি সিরিজে নতুন স্কোয়াড ঘোষণা, দলে চমক তরুণ পেসারদের",
                    "খেলাধুলা",
                    "আসন্ন আন্তর্জাতিক ক্রিকেট সিরিজের জন্য ঘোষিত বাংলাদেশ দলে জায়গা পেয়েছেন ঘরোয়া ক্রিকেটে আলো ছড়ানো বেশ কজন তরুণ উদীয়মান তারকা।",
                    "ঘরোয়া প্রিমিয়ার লিগ ও ঘরোয়া টি-টোয়েন্টি টুর্নামেন্টগুলোতে ধারাবাহিক পারফরম্যান্সের সুবাদে জাতীয় দলে ডাক পেয়েছেন বেশ কয়েকজন তরুণ ক্রিকেটার। নির্বাচকরা জানিয়েছেন, ভবিষ্যতের কথা মাথায় রেখে দলের বোলিং ও ব্যাটিং লাইনআপে তারুণ্যের শক্তি যুক্ত করা হয়েছে। আগামী সপ্তাহ থেকেই শুরু হবে মূল অনুশীলন ক্যাম্প। ক্রিকেটপ্রেমীদের মাঝেও নতুন এই স্কোয়াড নিয়ে ব্যাপক উদ্দীপনা লক্ষ্য করা যাচ্ছে।",
                    "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?auto=format&fit=crop&w=1200&q=80",
                    "স্পোর্টস রিপোর্টার", 1
                ),
                (
                    "বৈশ্বিক অর্থনীতিতে নতুন মোড়: জ্বালানি তেলের বাজারে স্থিতিশীলতার আভাস",
                    "অর্থনীতি",
                    "আন্তর্জাতিক বাজারে অপরিশোধিত জ্বালানি তেলের দাম কিছুটা হ্রাস পাওয়ায় স্বস্তির নিঃশ্বাস ফেলছে উন্নয়নশীল দেশগুলো।",
                    "বিশ্ব অর্থনীতির বর্তমান পরিস্থিতিতে প্রধান প্রধান অর্থনৈতিক শক্তিগুলোর মুদ্রানীতি এবং সরবরাহ শৃঙ্খলে বড় ধরনের পরিবর্তন লক্ষ্য করা যাচ্ছে। আন্তর্জাতিক বাজারে জ্বালানি তেলের দাম কিছুটা কমে যাওয়ায় আমদানি নির্ভর দেশগুলোর বৈদেশিক মুদ্রার রিজার্ভে চাপ কিছুটা কমবে বলে ধারণা করছেন অর্থনীতিবিদরা। দেশীয় বাজারেও এর ইতিবাচক প্রভাব পড়ার সম্ভাবনা রয়েছে।",
                    "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1200&q=80",
                    "অর্থনীতি ডেস্ক", 0
                )
            ]

            for item in demo_news:
                db.execute("""
                    INSERT INTO news
                    (title, category, summary, content, image,
                     author, featured, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (*item, datetime.now().strftime(
                    "%d %B %Y, %I:%M %p"
                )))


# ---------------- DESIGN ----------------

BASE = r"""
<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ page_title }} | NEWS24 BD</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#f3f4f6;color:#202124;
font-family:"Noto Sans Bengali","Nirmala UI",Arial,sans-serif}
a{color:inherit;text-decoration:none}
.top{background:#b60016;color:white;padding:8px 5%;
display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;
font-size:13px}
.brand{background:white;padding:20px 5%;display:flex;
align-items:center;justify-content:space-between;gap:15px;flex-wrap:wrap}
.logo{font-size:34px;font-weight:900;color:#c40019;letter-spacing:-1px}
.logo span{color:#202124}
.tagline{font-size:13px;color:#777}
.search{display:flex;gap:5px}
input,select,textarea{padding:11px;border:1px solid #d1d5db;
border-radius:5px;font:inherit;width:100%;margin:5px 0 12px}
.search input{width:200px;margin:0}
button,.btn{background:#c40019;color:white;border:0;padding:11px 16px;
border-radius:4px;cursor:pointer;font:inherit;display:inline-block}
nav{background:#151515;color:white;padding:0 5%;display:flex;
gap:0;overflow-x:auto;white-space:nowrap}
nav a{padding:14px 13px;font-size:14px}
nav a:hover{background:#c40019}
.breaking{background:#fff;border-bottom:1px solid #ddd;
padding:12px 5%;display:flex;gap:12px;align-items:center;overflow:hidden}
.breaking strong{background:#c40019;color:white;padding:8px 12px;
white-space:nowrap;font-size:13px}
.breaking a{font-size:14px;overflow:hidden;text-overflow:ellipsis}
.container{max-width:1200px;margin:24px auto;padding:0 18px}
.flash{padding:12px;background:#dcfce7;margin-bottom:15px;border-radius:5px;color:#166534}
.section-title{font-size:22px;border-left:5px solid #c40019;
padding-left:12px;margin:25px 0 16px}
.hero{display:grid;grid-template-columns:1.6fr 1fr;gap:18px}
.hero-main,.card,.panel{background:white;border-radius:6px;overflow:hidden;
box-shadow:0 2px 9px #0000000b}
.hero-main img{width:100%;height:340px;object-fit:cover}
.hero-main .info{padding:18px}
.hero-main h1{font-size:28px;margin:8px 0}
.hero-side{display:grid;gap:12px}
.side-item{display:grid;grid-template-columns:120px 1fr;gap:12px;
background:white;padding:10px;border-radius:5px}
.side-item img{width:120px;height:90px;object-fit:cover}
.side-item h3{font-size:16px;margin:4px 0}
.news-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.card img{width:100%;height:190px;object-fit:cover}
.card-info{padding:15px}
.card h3{margin:8px 0;font-size:19px;line-height:1.6}
.summary{color:#626262;line-height:1.8;font-size:14px}
.category{color:#c40019;font-size:13px;font-weight:bold}
.meta{color:#888;font-size:12px;margin-top:10px}
.article{background:white;padding:25px;border-radius:6px}
.article h1{font-size:32px;line-height:1.6}
.article img{width:100%;max-height:520px;object-fit:cover}
.article-body{font-size:18px;line-height:2.1;white-space:pre-line}
.share-box{margin:20px 0;padding:15px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:6px;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.share-box span{font-weight:bold;font-size:14px;margin-right:5px}
.share-btn{padding:8px 12px;border-radius:4px;color:white;font-size:13px;display:inline-flex;align-items:center;gap:5px;cursor:pointer;text-decoration:none;border:0}
.btn-fb{background:#1877f2}
.btn-wa{background:#25d366}
.btn-tw{background:#000000}
.btn-in{background:#0a66c2}
.btn-copy{background:#4b5563}
.panel{padding:22px;margin-bottom:20px}
.panel h2{margin-top:0}
.table-wrap{overflow-x:auto}
table{border-collapse:collapse;width:100%;background:white}
td,th{text-align:left;padding:11px;border-bottom:1px solid #eee}
th{background:#f4f4f4}
footer{background:#171717;color:#ddd;padding:30px 5%;margin-top:40px}
footer p{color:#aaa;font-size:13px}
.small-btn{padding:7px 10px;font-size:13px}
.danger{background:#a10d1e}
@media(max-width:750px){
 .hero{grid-template-columns:1fr}
 .hero-main img{height:230px}
 .news-grid{grid-template-columns:repeat(2,1fr);gap:10px}
 .card img{height:140px}
 .card-info{padding:10px}
 .card h3{font-size:16px}
 .article h1{font-size:24px}
 .logo{font-size:27px}
}
@media(max-width:450px){
 .news-grid{grid-template-columns:1fr}
 .search input{width:150px}
 .side-item{grid-template-columns:95px 1fr}
 .side-item img{width:95px;height:80px}
}
</style>
</head>
<body>
<div class="top">
 <span>বাংলাদেশের খবর, এক ঠিকানায়</span>
 <span>{{ today }}</span>
</div>
<header class="brand">
 <a class="logo" href="{{ url_for('home') }}">NEWS<span>24 BD</span></a>
 <div class="tagline">সত্যের সঙ্গে, সংবাদের পথে</div>
 <form class="search" action="{{ url_for('home') }}" method="get">
  <input name="q" placeholder="খবর খুঁজুন..." value="{{ query }}">
  <button>সার্চ</button>
 </form>
</header>
<nav>
 <a href="{{ url_for('home') }}">প্রচ্ছদ</a>
 {% for cat in categories %}
 <a href="{{ url_for('home', category=cat) }}">{{ cat }}</a>
 {% endfor %}
</nav>
<div class="breaking">
 <strong>ব্রেকিং নিউজ</strong>
 {% if breaking %}
 <a href="{{ url_for('article', news_id=breaking.id) }}">
 {{ breaking.title }}
 </a>
 {% else %}
 <a>কোনো ব্রেকিং নিউজ নেই</a>
 {% endif %}
</div>
<div class="container">
 {% with messages = get_flashed_messages() %}
 {% for message in messages %}
 <div class="flash">{{ message }}</div>
 {% endfor %}
 {% endwith %}
 {{ content|safe }}
</div>
<footer>
 <div class="logo">NEWS<span style="color:white">24 BD</span></div>
 <p>রাজনীতি, বাণিজ্য, খেলাধুলা, জাতীয়-আন্তর্জাতিক ব্রেকিং নিউজ, বিশ্লেষণমূলক সংবাদসহ যাবতীয় খবর পেতে চোখ রাখুন 'NEWS24 BD' তে ।</p>
 <p>ই-মেইল: web@news24bd.tv</p>
 <a href="{{ url_for('admin') }}">Admin Panel</a>
</footer>
</body>
</html>
"""


def page(content, **data):
    with get_db() as db:
        breaking = db.execute(
            "SELECT id, title FROM news ORDER BY id DESC LIMIT 1"
        ).fetchone()

    return render_template_string(
        BASE,
        content=render_template_string(content, **data),
        page_title=data.get("page_title", "সর্বশেষ সংবাদ"),
        categories=CATEGORIES,
        breaking=breaking,
        today=datetime.now().strftime("%d-%m-%Y"),
        query=request.args.get("q", "")
    )


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return func(*args, **kwargs)
    return wrapper


# ---------------- HOME PAGE ----------------

@app.route("/")
def home():
    category = request.args.get("category", "").strip()
    query = request.args.get("q", "").strip()

    sql = "SELECT * FROM news WHERE 1=1"
    params = []

    if category in CATEGORIES:
        sql += " AND category=?"
        params.append(category)

    if query:
        sql += " AND (title LIKE ? OR summary LIKE ? OR content LIKE ?)"
        term = "%" + query + "%"
        params.extend([term, term, term])

    sql += " ORDER BY featured DESC, id DESC"

    with get_db() as db:
        news_list = db.execute(sql, params).fetchall()

    featured = news_list[0] if news_list else None
    others = news_list[1:] if featured else []

    content = """
    {% if category or query %}
      <h2 class="section-title">
      {% if category %}{{ category }}{% else %}সার্চের ফলাফল{% endif %}
      {% if query %} — "{{ query }}"{% endif %}
      </h2>
    {% endif %}

    {% if featured and not category and not query %}
    <h2 class="section-title">আজকের প্রধান সংবাদ</h2>
    <div class="hero">
      <a class="hero-main" href="{{ url_for('article', news_id=featured.id) }}">
        {% if featured.image %}
        <img src="{{ featured.image }}" alt="{{ featured.title }}"
             onerror="this.style.display='none'">
        {% endif %}
        <div class="info">
          <span class="category">{{ featured.category }}</span>
          <h1>{{ featured.title }}</h1>
          <p class="summary">{{ featured.summary }}</p>
          <div class="meta">{{ featured.author }} | {{ featured.created_at }}</div>
        </div>
      </a>
      <div class="hero-side">
        {% for n in others[:3] %}
        <a class="side-item" href="{{ url_for('article', news_id=n.id) }}">
          {% if n.image %}
          <img src="{{ n.image }}" alt="{{ n.title }}"
               onerror="this.style.display='none'">
          {% endif %}
          <div>
            <span class="category">{{ n.category }}</span>
            <h3>{{ n.title }}</h3>
            <div class="meta">{{ n.created_at }}</div>
          </div>
        </a>
        {% endfor %}
      </div>
    </div>
    {% endif %}

    <h2 class="section-title">
      {% if category %}{{ category }} সংবাদ
      {% elif query %}খোঁজার ফলাফল
      {% else %}সর্বশেষ সংবাদ{% endif %}
    </h2>

    {% if news_list %}
    <div class="news-grid">
      {% for n in (news_list if category or query else others) %}
      <a class="card" href="{{ url_for('article', news_id=n.id) }}">
        {% if n.image %}
        <img src="{{ n.image }}" alt="{{ n.title }}"
             onerror="this.style.display='none'">
        {% endif %}
        <div class="card-info">
          <span class="category">{{ n.category }}</span>
          <h3>{{ n.title }}</h3>
          <p class="summary">{{ n.summary }}</p>
          <div class="meta">{{ n.created_at }}</div>
        </div>
      </a>
      {% endfor %}
    </div>
    {% else %}
      <div class="panel">কোনো সংবাদ পাওয়া যায়নি। অন্য শব্দ দিয়ে সার্চ করো।</div>
    {% endif %}
    """

    return page(
        content, news_list=news_list, featured=featured,
        others=others, category=category, query=query,
        page_title=category or "সর্বশেষ সংবাদ"
    )


# ---------------- NEWS DETAILS ----------------

@app.route("/news/<int:news_id>")
def article(news_id):
    with get_db() as db:
        n = db.execute(
            "SELECT * FROM news WHERE id=?", (news_id,)
        ).fetchone()

        if not n:
            abort(404)

        related = db.execute("""
            SELECT id, title, category, image, created_at
            FROM news WHERE category=? AND id<>?
            ORDER BY id DESC LIMIT 3
        """, (n["category"], news_id)).fetchall()

    content = """
    <article class="article">
      <span class="category">{{ n.category }}</span>
      <h1>{{ n.title }}</h1>
      <div class="meta">{{ n.author }} | প্রকাশ: {{ n.created_at }}</div>
      {% if n.image %}
      <img src="{{ n.image }}" alt="{{ n.title }}"
           onerror="this.style.display='none'">
      {% endif %}
      <h3>{{ n.summary }}</h3>
      <div class="article-body">{{ n.content }}</div>
      <p class="meta">সংবাদ বিভাগ: {{ n.category }}</p>

      <div class="share-box">
        <span>শেয়ার করুন:</span>
        <a href="https://www.facebook.com/sharer/sharer.php?u={{ request.url }}" target="_blank" class="share-btn btn-fb">Facebook</a>
        <a href="https://api.whatsapp.com/send?text={{ n.title }}%20-%20{{ request.url }}" target="_blank" class="share-btn btn-wa">WhatsApp</a>
        <a href="https://twitter.com/intent/tweet?text={{ n.title }}&url={{ request.url }}" target="_blank" class="share-btn btn-tw">X (Twitter)</a>
        <a href="https://www.linkedin.com/sharing/share-offsite/?url={{ request.url }}" target="_blank" class="share-btn btn-in">LinkedIn</a>
        <button onclick="navigator.clipboard.writeText(window.location.href); alert('লিংক কপি করা হয়েছে!');" class="share-btn btn-copy">📋 কপি লিংক</button>
      </div>
    </article>

    {% if related %}
    <h2 class="section-title">আরও পড়ুন</h2>
    <div class="news-grid">
      {% for item in related %}
      <a class="card" href="{{ url_for('article', news_id=item.id) }}">
        {% if item.image %}
        <img src="{{ item.image }}" alt="{{ item.title }}"
             onerror="this.style.display='none'">
        {% endif %}
        <div class="card-info">
          <span class="category">{{ item.category }}</span>
          <h3>{{ item.title }}</h3>
        </div>
      </a>
      {% endfor %}
    </div>
    {% endif %}
    """
    return page(content, n=n, related=related, page_title=n["title"])


# ---------------- ADMIN LOGIN ----------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin"))

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == ADMIN_USER and password == ADMIN_PASSWORD:
            session.clear()
            session["admin_logged_in"] = True
            return redirect(url_for("admin"))

        flash("Username অথবা password সঠিক নয়।")

    content = """
    <div class="panel" style="max-width:500px;margin:auto">
      <h2>Admin Login</h2>
      <form method="post">
        <label>Username</label>
        <input name="username" required>
        <label>Password</label>
        <input name="password" type="password" required>
        <button type="submit">Login</button>
      </form>
    </div>
    """
    return page(content, page_title="Admin Login")


# ---------------- ADMIN DASHBOARD ----------------

@app.route("/admin")
@login_required
def admin():
    with get_db() as db:
        news_list = db.execute(
            "SELECT * FROM news ORDER BY id DESC"
        ).fetchall()

    content = """
    <div class="panel">
      <h2>News Admin Panel</h2>
      <p>মোট সংবাদ: <b>{{ news_list|length }}</b></p>
      <a class="btn" href="{{ url_for('add_news') }}">+ Add News</a>
      <a class="btn" href="{{ url_for('admin_logout') }}">Logout</a>
    </div>

    <div class="panel">
      <h2>Manage News</h2>
      <div class="table-wrap">
      <table>
        <tr><th>ID</th><th>Title</th><th>Category</th><th>Action</th></tr>
        {% for n in news_list %}
        <tr>
          <td>{{ n.id }}</td>
          <td>{{ n.title }}</td>
          <td>{{ n.category }}</td>
          <td>
            <a class="btn small-btn"
               href="{{ url_for('edit_news', news_id=n.id) }}">Edit</a>
            <form method="post"
                  action="{{ url_for('delete_news', news_id=n.id) }}"
                  style="display:inline"
                  onsubmit="return confirm('Delete this news?')">
              <button class="danger small-btn">Delete</button>
            </form>
          </td>
        </tr>
        {% endfor %}
      </table>
      </div>
    </div>
    """
    return page(content, news_list=news_list, page_title="Admin")


# ---------------- ADD / EDIT NEWS ----------------

FORM_TEMPLATE = """
<div class="panel">
  <h2>{{ heading }}</h2>
  <form method="post">
    <label>News Title</label>
    <input name="title" value="{{ item.title if item else '' }}"
           maxlength="250" required>

    <label>Category</label>
    <select name="category" required>
      <option value="">ক্যাটাগরি নির্বাচন করুন</option>
      {% for c in categories %}
      <option value="{{ c }}"
        {% if item and item.category == c %}selected{% endif %}>
        {{ c }}
      </option>
      {% endfor %}
    </select>

    <label>Short Summary</label>
    <textarea name="summary" rows="3" required>{{ item.summary if item else '' }}</textarea>

    <label>Full News</label>
    <textarea name="content" rows="10" required>{{ item.content if item else '' }}</textarea>

    <label>Image URL (optional)</label>
    <input name="image" type="url"
           value="{{ item.image if item else '' }}">

    <label>Author / News Desk</label>
    <input name="author"
           value="{{ item.author if item else 'News Desk' }}">

    <label>
      <input type="checkbox" name="featured" value="1"
        style="width:auto"
        {% if item and item.featured %}checked{% endif %}>
      প্রধান সংবাদ হিসেবে দেখাও
    </label>
    <br><br>
    <button type="submit">{{ button_text }}</button>
    <a class="btn" href="{{ url_for('admin') }}">Cancel</a>
  </form>
</div>
"""


def save_news(item_id=None):
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "").strip()
    summary = request.form.get("summary", "").strip()
    content = request.form.get("content", "").strip()
    image = request.form.get("image", "").strip()
    author = request.form.get("author", "").strip() or "News Desk"
    featured = 1 if request.form.get("featured") == "1" else 0

    if not title or not summary or not content:
        flash("সব প্রয়োজনীয় তথ্য পূরণ করো।")
        return False

    if category not in CATEGORIES:
        flash("সঠিক ক্যাটাগরি নির্বাচন করো।")
        return False

    with get_db() as db:
        if item_id is None:
            db.execute("""
                INSERT INTO news
                (title, category, summary, content, image, author,
                 featured, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                title, category, summary, content, image, author,
                featured, datetime.now().strftime("%d %B %Y, %I:%M %p")
            ))
        else:
            db.execute("""
                UPDATE news SET title=?, category=?, summary=?, content=?,
                    image=?, author=?, featured=? WHERE id=?
            """, (
                title, category, summary, content, image,
                author, featured, item_id
            ))

    return True


@app.route("/admin/add", methods=["GET", "POST"])
@login_required
def add_news():
    if request.method == "POST":
        if save_news():
            flash("নতুন সংবাদ সফলভাবে প্রকাশ হয়েছে।")
            return redirect(url_for("admin"))

    return page(
        FORM_TEMPLATE, item=None, categories=CATEGORIES, heading="Add New News",
        button_text="Publish News", page_title="Add News"
    )


@app.route("/admin/edit/<int:news_id>", methods=["GET", "POST"])
@login_required
def edit_news(news_id):
    with get_db() as db:
        item = db.execute(
            "SELECT * FROM news WHERE id=?", (news_id,)
        ).fetchone()

    if not item:
        abort(404)

    if request.method == "POST":
        if save_news(news_id):
            flash("সংবাদ আপডেট হয়েছে।")
            return redirect(url_for("admin"))

        with get_db() as db:
            item = db.execute(
                "SELECT * FROM news WHERE id=?", (news_id,)
            ).fetchone()

    return page(
        FORM_TEMPLATE, item=item, categories=CATEGORIES, heading="Edit News",
        button_text="Save Changes", page_title="Edit News"
    )


@app.route("/admin/delete/<int:news_id>", methods=["POST"])
@login_required
def delete_news(news_id):
    with get_db() as db:
        db.execute("DELETE FROM news WHERE id=?", (news_id,))
    flash("সংবাদ মুছে ফেলা হয়েছে।")
    return redirect(url_for("admin"))


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("home"))


# ---------------- RUN ----------------

@app.errorhandler(404)
def not_found(error):
    return "Page not found (404)", 404


if __name__ == "__main__":
    init_db()
    print("NEWS24 BD is running!")
    print("Open http://127.0.0.1:5000 in Chrome.")
    app.run(debug=True)