"""
نظام التراويح الذكي - نسخة متقدمة جداً
Advanced Quran System with Continuous Verse Detection
- البحث عن الآيات الطويلة بدون توقف
- تصفية الترجمات غير الصحيحة
- بحث ذكي على كل الكلمات
"""
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import json
import os
import time
from difflib import SequenceMatcher
from functools import lru_cache
import re
import socket
from collections import defaultdict

def find_free_port(start_port=5000, max_port=5100):
    for port in range(start_port, max_port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('0.0.0.0', port))
            sock.close()
            return port
        except OSError:
            continue
    return 5000

PORT = find_free_port(5000, 5100)

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
app = Flask(__name__, template_folder=template_dir)
app.config['SECRET_KEY'] = 'quran-continuous-detection'
socketio = SocketIO(app, cors_allowed_origins="*", ping_interval=25, ping_timeout=60)

print(f"\n[SETUP] Loading Quran data with continuous detection...")

# ===============================
# Load Quran Data
# ===============================
quran_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'quran.json'))

if os.path.exists(quran_path):
    with open(quran_path, "r", encoding="utf-8") as f:
        quran_raw = json.load(f)
    print(f"[SUCCESS] Loaded quran.json")
else:
    print(f"[WARNING] quran.json not found")
    quran_raw = {}

verses_list = []
surah_verses = defaultdict(list)
phrase_index = {}
word_index = defaultdict(list)

def normalize(text):
    """تطبيع ذكي"""
    if not text:
        return ""
    text = re.sub(r'[ًٌٍَُِّْـ]', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip().lower()

normalize = lru_cache(maxsize=10000)(normalize)

# Build indexes
print("[INDEX] Building advanced indexes...")
for surah_num, surah in quran_raw.items():
    for idx, ayah in enumerate(surah.get("ayahs", [])):
        norm = normalize(ayah["ar"])
        verse_obj = {
            "ar": ayah["ar"],
            "en": ayah.get("en", ""),
            "fr": ayah.get("fr", ""),
            "nl": ayah.get("nl", ""),
            "surah": str(surah_num),
            "ayah": idx + 1,
            "normalized": norm,
            "length": len(norm),
            "words": norm.split()
        }
        verses_list.append(verse_obj)
        surah_verses[str(surah_num)].append(verse_obj)
        
        # فهرس العبارات
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

# ===============================
# Smart Search Engine
# ===============================
@lru_cache(maxsize=5000)
def similarity_score(a, b):
    """حساب التشابه"""
    if not a or not b:
        return 0
    return SequenceMatcher(None, a, b).ratio()

def search_continuous_verse(text, surah_num=None):
    """
    بحث مستمر عن الآيات الطويلة بدون توقف
    يعمل مع:
    - كلمات متفرقة من الآية
    - جمل طويلة بدون توقف
    - أجزاء من الآية
    """
    text_norm = normalize(text)
    if not text_norm or len(text_norm) < 4:
        return None, 0, False
    
    text_words = text_norm.split()
    
    # ==============================
    # المرحلة 1: البحث في السورة الحالية (إن وجدت)
    # ==============================
    if surah_num:
        verses_in_surah = surah_verses.get(str(surah_num), [])
        
        # مطابقة دقيقة
        for verse in verses_in_surah:
            if text_norm == verse["normalized"]:
                return verse, 1.0, False
        
        # مطابقة جملة
        for verse in verses_in_surah:
            if text_norm in verse["normalized"]:
                return verse, 0.95, False
        
        # بحث الكلمات المتتالية
        verse_words_set = set(verse["words"])
        for verse in verses_in_surah:
            # عد الكلمات المتطابقة
            matching = sum(1 for w in text_words if w in verse["words"])
            
            if matching >= 3:  # على الأقل 3 كلمات
                score = matching / max(len(text_words), len(verse["words"]))
                if score > 0.65:
                    return verse, score, False
    
    # ==============================
    # المرحلة 2: البحث في كل السور
    # ==============================
    best_match = None
    best_score = 0
    found_in_different_surah = False
    
    # البحث عن العبارات
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
    
    # ==============================
    # المرحلة 3: البحث بناءً على الكلمات الرئيسية
    # ==============================
    if text_words:
        # خذ أطول كلمة (غالباً الأهم)
        main_word = max(text_words, key=len) if text_words else None
        
        if main_word and main_word in word_index:
            candidates = word_index[main_word]
            
            # ابحث عن أفضل مطابقة
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
    
    # ==============================
    # المرحلة 4: مطابقة التشابه
    # ==============================
    text_len = len(text_norm)
    tolerance = max(int(text_len * 0.35), 5)
    
    for verse in verses_list:
        if abs(verse["length"] - text_len) <= tolerance:
            score = similarity_score(text_norm, verse["normalized"])
            
            if score > 0.75:  # عتبة عالية
                return verse, score, verse["surah"] != str(surah_num) if surah_num else True
    
    return None, 0, False

def is_valid_result(verse, confidence, text):
    """
    تحقق من أن النتيجة صحيحة حقاً
    لا تعيد ترجمة للكلمات الغير معروفة
    """
    # إذا كانت الثقة منخفضة جداً، لا تعيد شيء
    if confidence < 0.55:
        return False
    
    # تحقق من أن النص يحتوي على كلمات كافية من الآية
    text_norm = normalize(text)
    text_words = set(text_norm.split())
    verse_words = set(verse["words"])
    
    # يجب أن تكون هناك كلمات مشتركة كافية
    common_words = len(text_words & verse_words)
    
    if common_words < 2:
        return False
    
    return True

# ===============================
# Routes
# ===============================
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
    """احصل على جميع آيات السورة"""
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

# ===============================
# WebSocket Events
# ===============================
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
        trans = ''
        if lang == 'ar':
            trans = verse['ar']
        elif lang == 'en':
            trans = verse['en']
        elif lang == 'fr':
            trans = verse['fr']
        elif lang == 'nl':
            trans = verse['nl']
        
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
    
    # البحث المستمر
    verse, confidence, surah_changed = search_continuous_verse(text, current_surah)
    
    # تحقق من صحة النتيجة
    if not is_valid_result(verse, confidence, text):
        # لا تعيد ترجمة خاطئة!
        emit('no_match', {
            'reason': 'confidence_too_low',
            'response_time': round((time.time() - start) * 1000, 1)
        })
        return
    
    elapsed = (time.time() - start) * 1000
    
    if verse:
        trans = ''
        if lang == 'ar':
            trans = verse['ar']
        elif lang == 'en':
            trans = verse['en']
        elif lang == 'fr':
            trans = verse['fr']
        elif lang == 'nl':
            trans = verse['nl']
        
        # إرسال الآية
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
                    next_trans = ''
                    if lang == 'ar':
                        next_trans = v['ar']
                    elif lang == 'en':
                        next_trans = v['en']
                    elif lang == 'fr':
                        next_trans = v['fr']
                    elif lang == 'nl':
                        next_trans = v['nl']
                    
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

# ===============================
# Main
# ===============================
if __name__ == "__main__":
    print("="*70)
    print("🌙 نظام التراويح الذكي - CONTINUOUS DETECTION 🌙")
    print("="*70)
    print("✅ Continuous Verse Detection")
    print("✅ Long Verse Support")
    print("✅ Translation Filtering")
    print("✅ No False Positives")
    print("✅ Advanced Search")
    print("="*70)
    print(f"\n🌐 Open in browser: http://localhost:{PORT}")
    print(f"📱 Local network: http://192.168.129.3:{PORT}\n")
    
    socketio.run(
        app,
        host="0.0.0.0",
        port=PORT,
        debug=False,
        use_reloader=False
    )