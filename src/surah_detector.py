"""
سورة ديتيكتور - Surah Detection Module
تعرّف على السورة من الآيات الأولى
يدعم حفص وورش
"""
import json
import re
from typing import Tuple, Optional, Dict

# ===============================
# Load Quran Data
# ===============================
with open("data/quran.json", "r", encoding="utf-8") as f:
    quran_data = json.load(f)

# ===============================
# Surah Names Database
# ===============================
SURAH_NAMES = {
    "1": {"ar": "الفاتحة", "en": "Al-Fatihah"},
    "2": {"ar": "البقرة", "en": "Al-Baqarah"},
    "3": {"ar": "آل عمران", "en": "Al-Imran"},
    "4": {"ar": "النساء", "en": "An-Nisa"},
    "5": {"ar": "المائدة", "en": "Al-Maidah"},
    "6": {"ar": "الأنعام", "en": "Al-Anam"},
    "7": {"ar": "الأعراف", "en": "Al-Araf"},
    "8": {"ar": "الأنفال", "en": "Al-Anfal"},
    "9": {"ar": "التوبة", "en": "At-Tawbah"},
    "10": {"ar": "يونس", "en": "Yunus"},
    # ... (full list would be all 114 surahs)
}

# Quran Initials (الفواتح) for quick detection
QURAN_INITIALS = {
    "الم": "2",        # البقرة
    "الم": "3",        # آل عمران
    "الم": "29",       # العنكبوت
    "الم": "30",       # الروم
    "الم": "31",       # لقمان
    "الم": "32",       # السجدة
    "الر": "10",       # يونس
    "الر": "11",       # هود
    "الر": "12",       # يوسف
    "الر": "13",       # الرعد
    "الر": "14",       # إبراهيم
    "الر": "15",       # الحجر
    "المص": "7",       # الأعراف
    "المر": "13",      # الرعد
    "كهيعص": "19",     # مريم
    "طه": "20",        # طه
    "طسم": "26",       # الشعراء
    "يس": "36",        # يس
    "ص": "38",         # ص
    "ح": "40",         # غافر
    "عسق": "42",       # الشورى
    "ن": "68",         # القلم
}

# Known first verses for each Surah
SURAH_FIRST_VERSES = {
    "1": "الحمد لله رب العالمين",
    "2": "الم ذلك الكتاب لا ريب فيه",
    "3": "الم الله لا إله إلا هو الحي القيوم",
    "4": "يا أيها الناس اتقوا ربكم الذي خلقكم من نفس واحدة",
    "5": "يا أيها الذين آمنوا أوفوا بالعقود",
    "6": "الحمد لله الذي خلق السموات والأرض",
    # ... (full list)
}

def normalize_text(text: str) -> str:
    """تطبيع النص - Remove diacritics and special characters."""
    text = re.sub(r'[ًٌٍَُِّْـ]', '', text)  # Remove diacritics
    text = re.sub(r'[^\w\s]', '', text)       # Remove special chars
    return text.strip()

def detect_surah_from_initials(text: str) -> Optional[str]:
    """
    كشف السورة من الفواتح (Initials)
    مثال: الم → البقرة أو آل عمران أو العنكبوت
    """
    normalized = normalize_text(text)
    
    # Check for known initials
    for initial, surah_num in QURAN_INITIALS.items():
        if initial in normalized:
            return surah_num
    
    return None

def similarity(a: str, b: str) -> float:
    """حساب التشابه بين نصين."""
    from difflib import SequenceMatcher
    if not a or not b:
        return 0
    return SequenceMatcher(None, a, b).ratio()

def detect_surah_from_first_verse(text: str, threshold: float = 0.60) -> Optional[str]:
    """
    كشف السورة من الآية الأولى
    يقارن مع أول آية في كل سورة
    """
    normalized = normalize_text(text)
    best_match = None
    best_score = 0
    
    for surah_num, first_verse in SURAH_FIRST_VERSES.items():
        first_verse_normalized = normalize_text(first_verse)
        score = similarity(normalized, first_verse_normalized)
        
        if score > best_score:
            best_score = score
            best_match = surah_num
    
    if best_score > threshold:
        return best_match
    
    return None

def detect_surah_context(text: str) -> Optional[str]:
    """
    كشف السورة من السياق
    يبحث عن كلمات شهيرة في بداية السور
    مثل: يا أيها الذين آمنوا (في عدة سور)
    """
    normalized = normalize_text(text)
    
    context_keywords = {
        "2": ["يا أيها الناس", "يا بني إسرائيل"],
        "3": ["يا مريم"],
        "4": ["يا أيها الناس اتقوا"],
        "5": ["يا أيها الذين آمنوا"],
        # ... etc
    }
    
    for surah_num, keywords in context_keywords.items():
        for keyword in keywords:
            if keyword in text:
                return surah_num
    
    return None

def detect_surah(text: str) -> Tuple[Optional[str], str]:
    """
    نظام كشف السورة المتعدد المستويات
    جرب:
    1. الفواتح (الم، الر، إلخ)
    2. الآية الأولى
    3. السياق
    4. الكلمات المفتاحية
    
    Returns:
        (surah_number, detection_method)
    """
    # Level 1: Check initials
    surah = detect_surah_from_initials(text)
    if surah:
        return surah, "initials"
    
    # Level 2: Check first verse
    surah = detect_surah_from_first_verse(text, threshold=0.70)
    if surah:
        return surah, "first_verse"
    
    # Level 3: Check context
    surah = detect_surah_context(text)
    if surah:
        return surah, "context"
    
    return None, "no_detection"

# ===============================
# Sequential Prediction System
# ===============================
class SequentialAyahPredictor:
    """
    نظام توقع الآيات التسلسلي
    يتتبع الآية الحالية ويتنبأ بالتالية
    """
    
    def __init__(self):
        self.current_surah = None
        self.current_ayah_index = None
        self.surah_verses = None
        self.last_matched_ayah = None
        
    def set_surah(self, surah_num: str):
        """تعيين السورة الحالية."""
        self.current_surah = surah_num
        self.surah_verses = quran_data[surah_num]["ayahs"]
        self.current_ayah_index = 0
        print(f"[SURAH] Set to Surah {surah_num}: {SURAH_NAMES[surah_num]['ar']}")
        
    def reset(self):
        """إعادة تهيئة (عند الركوع)."""
        self.current_surah = None
        self.current_ayah_index = None
        self.surah_verses = None
        self.last_matched_ayah = None
        print("[RESET] Ayah predictor reset")
        
    def predict_next_ayah(self) -> Optional[Dict]:
        """
        التنبؤ بالآية التالية مباشرة
        بدون البحث في كل المصحف
        """
        if not self.current_surah or not self.surah_verses:
            return None
        
        if self.current_ayah_index >= len(self.surah_verses) - 1:
            return None  # No more verses in this surah
        
        next_index = self.current_ayah_index + 1
        next_ayah = self.surah_verses[next_index]
        
        return {
            "ar": next_ayah["ar"],
            "en": next_ayah.get("en", ""),
            "fr": next_ayah.get("fr", ""),
            "nl": next_ayah.get("nl", ""),
            "surah": self.current_surah,
            "ayah": next_index + 1,
            "is_prediction": True
        }
    
    def match_and_advance(self, text: str, threshold: float = 0.50) -> Tuple[Optional[Dict], float]:
        """
        طابق النص وتقدم للآية التالية
        يبحث فقط داخل السورة الحالية
        """
        if not self.current_surah or not self.surah_verses:
            return None, 0
        
        normalized = normalize_text(text)
        best_match = None
        best_score = 0
        best_index = None
        
        # Search only in current surah
        for i, ayah in enumerate(self.surah_verses):
            ayah_normalized = normalize_text(ayah["ar"])
            score = similarity(normalized, ayah_normalized)
            
            if score > best_score:
                best_score = score
                best_match = ayah
                best_index = i
        
        # Advance to next if match found
        if best_score > threshold and best_index is not None:
            self.current_ayah_index = best_index
            self.last_matched_ayah = best_match
            print(f"[MATCH] Advanced to ayah {best_index + 1} in Surah {self.current_surah}")
            return best_match, best_score
        
        return None, best_score
    
    def get_ayah_info(self, ayah_index: int) -> Optional[Dict]:
        """احصل على معلومات آية محددة."""
        if not self.surah_verses or ayah_index >= len(self.surah_verses):
            return None
        
        ayah = self.surah_verses[ayah_index]
        return {
            "ar": ayah["ar"],
            "en": ayah.get("en", ""),
            "fr": ayah.get("fr", ""),
            "nl": ayah.get("nl", ""),
            "surah": self.current_surah,
            "ayah": ayah_index + 1
        }

# ===============================
# Optimized Recitation Matcher
# ===============================
class OptimizedRecitationMatcher:
    """
    محقق التراويح المحسّن
    يدمج كشف السورة + التنبؤ التسلسلي
    """
    
    def __init__(self):
        self.predictor = SequentialAyahPredictor()
        self.consecutive_matches = 0
        
    def process_recognized_text(self, text: str) -> Dict:
        """
        معالجة النص المعترف به
        إذا كانت السورة مكتشفة، استخدم التنبؤ التسلسلي
        وإلا، حاول كشف السورة أولاً
        """
        result = {
            "matched_ayah": None,
            "predicted_next": None,
            "surah": None,
            "status": "no_match",
            "confidence": 0
        }
        
        # If no surah detected yet, try to detect
        if not self.predictor.current_surah:
            surah_num, method = detect_surah(text)
            if surah_num:
                self.predictor.set_surah(surah_num)
                result["surah"] = surah_num
                result["detection_method"] = method
                print(f"[DETECTION] Surah detected by {method}: {surah_num}")
        
        # Try to match in current surah
        if self.predictor.current_surah:
            matched, score = self.predictor.match_and_advance(text, threshold=0.45)
            if matched:
                result["matched_ayah"] = matched
                result["confidence"] = round(score, 2)
                result["status"] = "matched_in_surah"
                self.consecutive_matches += 1
                
                # Predict next ayah
                next_ayah = self.predictor.predict_next_ayah()
                if next_ayah:
                    result["predicted_next"] = next_ayah
                
                print(f"[SEQUENTIAL] Match #{self.consecutive_matches} in {result['surah']}")
        
        return result
    
    def on_ruku(self):
        """عند الركوع - إعادة تهيئة."""
        print(f"[RUKU] End of rakah - resetting after {self.consecutive_matches} consecutive matches")
        self.predictor.reset()
        self.consecutive_matches = 0
