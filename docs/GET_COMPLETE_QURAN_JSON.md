# 📖 How to Get Complete Quran.json File

## ❌ المشكلة (The Problem):

```
[MATCHER] Loaded 7 verses from Quran  ← يجب أن يكون 6236!
```

ملفك `data/quran.json` يحتوي على سورة واحدة فقط (الفاتحة) بـ 7 آيات.
أنت تحتاج ملف كامل بـ **114 سورة و 6236 آية**!

---

## ✅ الحل (Solutions):

### الطريقة الأولى: تحميل من مصدر موثوق ⭐ (الأفضل)

#### **1. من Quran.com API:**

```bash
# تحميل كامل Quran مع الترجمات
curl https://api.quran.com/api/v4/quran/verses/uthmani > quran_temp.json

# أو استخدم Python:
python3 << 'EOF'
import json
import urllib.request

print("جاري التحميل من Quran.com...")
try:
    url = "https://api.quran.com/api/v4/quran/verses/uthmani?language=en&fields=text_uthmani,translations"
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode())
        print(f"✓ تم تحميل {len(data.get('verses', []))} آية")
except Exception as e:
    print(f"✗ خطأ: {e}")
EOF
```

#### **2. من GitHub (جاهز تماماً):**

**تحميل مباشر (الأسهل):**

```bash
# Windows PowerShell:
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/rn0x/quran-json/master/quran.json" -OutFile "data\quran.json"

# Mac/Linux:
curl -o data/quran.json https://raw.githubusercontent.com/rn0x/quran-json/master/quran.json
```

**أو من مصدر آخر:**

```bash
# مصدر بديل:
curl -o data/quran.json https://raw.githubusercontent.com/semarketir/quranjson/master/site/quran.json
```

#### **3. من IslamicAPI:**

```bash
# مصدر متخصص للقرآن:
curl "https://api.islamic.network/quran/chapters" > quran_metadata.json
```

---

## 🛠️ حل سريع (Quick Fix):

### استخدم ملف Quran JSON جاهز:

```python
# save as: download_quran.py
import json
import urllib.request
import sys

print("⏳ جاري تحميل القرآن الكريم...")
print("Loading complete Quran with 114 Surahs and 6236 Ayahs...")

urls = [
    "https://raw.githubusercontent.com/rn0x/quran-json/master/quran.json",
    "https://cdn.jsdelivr.net/gh/rn0x/quran-json@master/quran.json"
]

success = False
for url in urls:
    try:
        print(f"\nحاول من: {url}")
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            
            # تحقق من أن البيانات كاملة
            if isinstance(data, dict) and len(data) >= 114:
                with open('data/quran.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                # احسب إجمالي الآيات
                total_ayahs = sum(len(surah.get('ayahs', [])) 
                                for surah in data.values() 
                                if isinstance(surah, dict))
                
                print(f"\n✅ نجح التحميل!")
                print(f"   📊 {len(data)} سورة")
                print(f"   📝 {total_ayahs} آية")
                print(f"   💾 حفظ في: data/quran.json")
                success = True
                break
    except Exception as e:
        print(f"   ✗ فشل: {e}")
        continue

if not success:
    print("\n❌ فشل التحميل من جميع المصادر")
    print("حاول يدويًا:")
    print("1. اذهب إلى: https://github.com/rn0x/quran-json")
    print("2. ثبّت repo أو حمّل quran.json مباشرة")
    sys.exit(1)
```

**شغّله:**
```bash
python download_quran.py
```

---

## 📍 خيارات اليدوية (Manual Options):

### 1. من GitHub Desktop:

```
1. https://github.com/rn0x/quran-json
2. Clone أو Download ZIP
3. انسخ quran.json إلى data/ مجلدك
```

### 2. من موقع مباشر:

- **https://cdn.jsdelivr.net/gh/rn0x/quran-json@master/quran.json**
- **https://quran-api.pages.dev/data/quran.json**

### 3. استخدم API مباشرة:

```python
# في app.py، غيّر كود تحميل البيانات:

import requests

def load_quran_from_api():
    """تحميل من API بدل ملف JSON"""
    url = "https://api.quran.com/api/v4/chapters?language=en"
    response = requests.get(url)
    return response.json()
```

---

## ✔️ التحقق من الملف:

بعد التحميل، تأكد:

```python
import json

with open('data/quran.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    
    print(f"Surahs: {len(data)}")
    
    total_ayahs = 0
    for surah in data.values():
        if isinstance(surah, dict) and 'ayahs' in surah:
            total_ayahs += len(surah['ayahs'])
    
    print(f"Total Ayahs: {total_ayahs}")
    
    if len(data) == 114 and total_ayahs == 6236:
        print("✅ ملف صحيح تماماً!")
    else:
        print(f"⚠️ قد يكون الملف ناقص: {len(data)} سورة, {total_ayahs} آية")
```

**يجب أن تشاهد:**
```
Surahs: 114
Total Ayahs: 6236
✅ ملف صحيح تماماً!
```

---

## 🚀 خطوات سريعة:

### Step 1: تحميل الملف

**Windows PowerShell:**
```powershell
mkdir data -Force
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/rn0x/quran-json/master/quran.json" -OutFile "data\quran.json"
```

**Mac/Linux:**
```bash
mkdir -p data
curl -o data/quran.json https://raw.githubusercontent.com/rn0x/quran-json/master/quran.json
```

### Step 2: تحقق من التحميل

```bash
python3 << 'EOF'
import json
with open('data/quran.json') as f:
    d = json.load(f)
    ayahs = sum(len(s.get('ayahs', [])) for s in d.values() if isinstance(s, dict))
    print(f"✓ {len(d)} Surahs, {ayahs} Ayahs")
EOF
```

### Step 3: شغّل التطبيق

```bash
python app.py
```

**يجب أن ترى:**
```
[MATCHER] Loaded 6236 verses from Quran  ✅
```

---

## 📋 قائمة المصادر الموثوقة (Reliable Sources):

| المصدر | النوع | الحجم | الملاحظات |
|---|---|---|---|
| rn0x/quran-json | GitHub | ~3MB | كامل + تعليقات |
| quran.com API | API | Dynamic | محدث باستمرار |
| quran-api | Static | ~2MB | سريع وموثوق |
| islamicAPI | API | Dynamic | متخصصة |

---

## ⚠️ إذا لم ينجح:

### مشكلة: تحميل بطيء جداً

```bash
# استخدم wget بدل curl (أسرع):
wget https://raw.githubusercontent.com/rn0x/quran-json/master/quran.json -O data/quran.json
```

### مشكلة: الملف ناقص

```bash
# تحقق من الملف:
ls -lh data/quran.json
# يجب أن يكون ~3-5 MB

# إذا صغير جداً (< 100KB):
rm data/quran.json
# حمّل مرة أخرى
```

### مشكلة: خطأ JSON

```python
# اختبر صحة JSON:
python -m json.tool data/quran.json > /dev/null && echo "✓ Valid" || echo "✗ Invalid"
```

---

## 🎯 النتيجة المتوقعة:

بعد استبدال الملف:

```bash
python app.py

# Output:
[MATCHER] Loaded 6236 verses from Quran  ✅
🌙 TARAWEEH RECOGNIZER - SEQUENTIAL PREDICTION 🌙
✅ Using faster_whisper (tiny model)
✅ Sequential Ayah Prediction
✅ Surah Auto-Detection

Running on http://0.0.0.0:5000
```

---

## 📞 خيار أخير (Last Resort):

إذا أردت قاعدة بيانات كاملة:

```bash
# استخدم Docker + MongoDB مع بيانات قرآن:
docker pull qcms/quran
```

أو استخدم قاعدة البيانات المدمجة:

```python
# pip install quran
from quran import Quran
quran = Quran()
verses = quran.get_verses()  # 6236 verse!
```

---

## ✅ الخلاصة:

```
الملف الحالي: 7 آيات ❌
الملف المطلوب: 6236 آية ✅

الحل: تحميل واحد من المصادر أعلاه
الوقت: < 1 دقيقة
النتيجة: نظام عاملة بكفاءة!
```

---

**اختر الطريقة الأولى (GitHub) - الأسهل والأسرع! ⭐**

بعد التحميل، شغّل `python app.py` مرة أخرى وسترى الفرق! 🚀
