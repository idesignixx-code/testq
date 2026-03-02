"""
نظام التراويح الذكي - نسخة متقدمة جداً
Advanced Quran System with Continuous Verse Detection
البحث عن الآيات الطويلة بدون توقف
تصفية الترجمات غير الصحيحة
بحث ذكي على كل الكلمات
"""
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import json
import os
import time
from difflib import SequenceMatcher
from functools import lru_cache
import re
from collections import defaultdict

# ==============================
# Render/Production Configuration
# ==============================
PORT = int(os.environ.get("PORT", 5000))  # Render provides PORT env var

# Get absolute path to project root (where app.py is located)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'quran-continuous-detection')

# SocketIO with production settings
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    ping_interval=25, 
    ping_timeout=60,
    async_mode='eventlet'
)

print(f"\n[SETUP] Loading Quran data with continuous detection...")

# ==============================
# Load Quran Data
# ==============================
quran_path = os.path.join(BASE_DIR, 'data', 'quran.json')

if os.path.exists(quran_path):
    with open(quran_path, "r", encoding="utf-8") as f:
        quran_raw = json.load(f)
    print(f"[SUCCESS] Loaded quran.json from {quran_path}")
else:
    print(f"[ERROR] quran.json not found at {quran_path}")
    quran_raw = {}

verses_list = []
surah_verses = defaultdict(list)
phrase_index = {}
word_index = defaultdict(list)

@lru_cache(maxsize=10000)
def normalize(text):
    """تطبيع ذكي"""
    if not text:
        return ""
    text = re.sub(r'[ًٌٍَُِّْـ]', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip().lower()

# ==============================
# Build Indexes
# ==============================
print("[INDEX] Building advanced indexes...")

for surah_num, surah in quran_raw.items():
    for idx, ayah in enumerate(surah.get("ayahs", [])):
        norm = normalize(ayah["ar"])
        verse_obj = {
            "ar": ayah["ar"],
            "en": ayah.get("en", " "),
            "fr": ayah.get("fr", " "),
            "nl": ayah.get("nl", " "),
            "surah": str(surah_num),
            "ayah": idx + 1,
            "normalized": norm,
            "length": len(norm),
            "words": norm.split()
        }
        verses_list.append(verse_obj)
        surah_verses[str(surah_num)].append(verse_obj)
        
        # فهرس العبارات (3 كلمات)
        words = norm.split()
        for i in range(len(words) - 2):
            phrase = " ".join(words[i:i+3])
            if phrase not in phrase_index:
                phrase_index[phrase] = []
            phrase_index[phrase].append(verse_obj)
        
        # فهرس الكلمات
        for word in words:
            if len(word) > 2:
                word_index[word].append(verse_obj)

print(f"[DATA] Loaded {len(verses_list)} verses")
print(f"[INDEX] Built phrase and word indexes\n")

# ==============================
# Smart Search Engine
# ==============================
@lru_cache(maxsize=5000)
def similarity_score(a, b):
    """حساب التشابه"""
    if not a or not b:
        return 0
    return SequenceMatcher(None, a, b).ratio()

def search_continuous_verse(text, surah_num=None):
    """بحث مستمر عن الآيات الطويلة بدون توقف"""
    text_norm = normalize(text)
    if not text_norm or len(text_norm) < 4:
        return None, 0, False
    
    text_words = text_norm.split()

    # المرحلة 1: البحث في السورة الحالية
    if surah_num:
        verses_in_surah = surah_verses.get(str(surah_num), [])
        
        for verse in verses_in_surah:
            if text_norm == verse["normalized"]:
                return verse, 1.0, False
        
        for verse in verses_in_surah:
            if text_norm in verse["normalized"]:
                return verse, 0.95, False
        
        for verse in verses_in_surah:
            matching = sum(1 for w in text_words if w in verse["words"])
            if matching >= 3:
                score = matching / max(len(text_words), len(verse["words"]))
                if score > 0.65:
                    return verse, score, False

    # المرحلة 2: البحث في كل السور عبر العبارات
    best_match = None
    best_score = 0
    found_in_different_surah = False

    for phrase, verses in phrase_index.items():
        phrase_words = phrase.split()
        matching = sum(1 for w in text_words if w in phrase_words)
        if matching >= 2:
            score = matching / max(len(text_words), len(phrase_words))
            if score > best_score:
                best_score = score
                best_match = verses[0] if verses else None
                found_in_different_surah = True

    if best_score > 0.65:
        return best_match, best_score, found_in_different_surah

    # المرحلة 3: البحث بالكلمات الرئيسية
    if text_words:
        main_word = max(text_words, key=len) if text_words else None
        if main_word and main_word in word_index:
            candidates = word_index[main_word]
            for verse in candidates:
                matching = sum(1 for w in text_words if w in verse["words"])
                if matching >= 2:
                    score = matching / max(len(text_words), len(verse["words"]))
                    if score > best_score:
                        best_score = score
                        best_match = verse
                        found_in_different_surah = verse["surah"] != str(surah_num) if surah_num else True

    if best_score > 0.55:
        return best_match, best_score, found_in_different_surah

    # المرحلة 4: مطابقة التشابه
    text_len = len(text_norm)
    tolerance = max(int(text_len * 0.35), 5)

    for verse in verses_list:
        if abs(verse["length"] - text_len) <= tolerance:
            score = similarity_score(text_norm, verse["normalized"])
            if score > 0.75:
                return verse, score, verse["surah"] != str(surah_num) if surah_num else True

    return None, 0, False

def is_valid_result(verse, confidence, text):
    """تحقق من أن النتيجة صحيحة"""
    if confidence < 0.55:
        return False
    text_norm = normalize(text)
    text_words = set(text_norm.split())
    verse_words = set(verse["words"])
    common_words = len(text_words & verse_words)
    return common_words >= 2

# ==============================
# Routes
# ==============================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/reader")
def reader():
    lang = request.args.get("lang", "ar")
    return render_template("reader.html", lang=lang)

@app.route("/translation")
def translation():
    lang = request.args.get("lang", "ar")
    return render_template("translation_only.html", lang=lang)

@app.route("/api/surah/<surah_num>")
def get_surah(surah_num):
    verses_in_surah = surah_verses.get(str(surah_num), [])
    if not verses_in_surah:
        return jsonify({"status": "error"}), 404
    return jsonify({
        "surah": surah_num,
        "verses": [
            {
                "ayah": v["ayah"],
                "ar": v["ar"],
                "en": v["en"],
                "fr": v["fr"],
                "nl": v["nl"]
            }
            for v in verses_in_surah
        ]
    })

@app.route("/api/verses")
def get_all_verses():
    return jsonify({
        "total_verses": len(verses_list),
        "total_surahs": len(surah_verses)
    })

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "verses_loaded": len(verses_list),
        "port": PORT
    })

# ==============================
# WebSocket Events
# ==============================
@socketio.on('connect')
def handle_connect():
    print("[SOCKET] Client connected")
    emit('status', {'connected': True})

@socketio.on('stream_surah')
def handle_stream_surah(data):
    """بث آيات السورة"""
    surah_num = data.get('surah')
    lang = data.get('lang', 'ar')
    if not surah_num:
        return
    verses_in_surah = surah_verses.get(str(surah_num), [])
    if not verses_in_surah:
        emit('error', {'message': 'Surah not found'})
        return
    
    verses_data = []
    for verse in verses_in_surah:
        trans = verse.get(lang, verse['ar'])
        verses_data.append({
            "ayah": verse["ayah"],
            "ar": verse["ar"],
            "translation": trans
        })
    
    emit('surah_stream', {
        'surah': surah_num,
        'verses': verses_data
    }, broadcast=True)

@socketio.on('recognize_verse')
def handle_recognize(data):
    """تعرف مستمر على الآيات الطويلة"""
    start = time.time()
    text = data.get('text', '').strip()
    current_surah = data.get('surah')
    lang = data.get('lang', 'ar')
    
    if not text or len(text) < 4:
        return

    verse, confidence, surah_changed = search_continuous_verse(text, current_surah)

    if not is_valid_result(verse, confidence, text):
        emit('no_match', {
            'reason': 'confidence_too_low',
            'response_time': round((time.time() - start) * 1000, 1)
        })
        return

    elapsed = (time.time() - start) * 1000

    if verse:
        trans = verse.get(lang, verse['ar'])
        
        emit('current_verse_update', {
            'verse': {
                'ayah': verse['ayah'],
                'ar': verse['ar'],
                'translation': trans
            },
            'surah': verse['surah'],
            'confidence': round(confidence, 2),
            'surah_changed': surah_changed,
            'response_time': round(elapsed, 1)
        }, broadcast=True)
        
        # إرسال الآيات التالية
        verses_in_surah = surah_verses.get(verse['surah'], [])
        next_verses_data = []
        
        for i in range(int(verse['ayah']) + 1, min(int(verse['ayah']) + 4, len(verses_in_surah) + 1)):
            for v in verses_in_surah:
                if v['ayah'] == i:
                    next_trans = v.get(lang, v['ar'])
                    next_verses_data.append({
                        'ayah': v['ayah'],
                        'ar': v['ar'],
                        'translation': next_trans
                    })
                    break
        
        if next_verses_data:
            emit('next_verses_streaming', {
                'surah': verse['surah'],
                'verses': next_verses_data,
                'current_ayah': verse['ayah']
            }, broadcast=True)

# ==============================
# Gunicorn/Render Compatibility (CRITICAL)
# ==============================
# This variable is required for Render to find your app
application = app

# ==============================
# Local Development Only
# ==============================
if __name__ == "__main__":
    print("="*70)
    print("🌙 نظام التراويح الذكي - CONTINUOUS DETECTION 🌙")
    print("="*70)
    print(f"\n🌐 Open in browser: http://localhost:{PORT}\n")
    
    socketio.run(
        app,
        host="0.0.0.0",
        port=PORT,
        debug=False,
        use_reloader=False
    )
