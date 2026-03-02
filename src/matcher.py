"""
محقق الآيات المحسّن مع التنبؤ التسلصلي والكاش
Enhanced Ayah Matcher with Sequential Prediction & Caching
"""
import json
import re
from difflib import SequenceMatcher
from typing import Tuple, Optional, Dict, List
from functools import lru_cache
import time

# ===============================
# Helper Functions (DEFINE FIRST!)
# ===============================
@lru_cache(maxsize=1000)
def normalize_text(text: str) -> str:
    """تطبيع النص - Remove diacritics (CACHED)."""
    text = re.sub(r'[ًٌٍَُِّْـ]', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()

def similarity(a: str, b: str) -> float:
    """حساب التشابه."""
    if not a or not b:
        return 0
    return SequenceMatcher(None, a, b).ratio()

# ===============================
# Load Quran Data (once at startup)
# ===============================
print("[LOADING] Loading Quran data...")
start_load = time.time()

with open("data/quran.json", "r", encoding="utf-8") as f:
    quran_data = json.load(f)

# Pre-index all verses with optimization
all_ayahs = []
surah_lookup = {}
normalized_index = {}  # For fast exact match lookup

for surah_num, surah in quran_data.items():
    surah_lookup[surah_num] = []
    for ayah_idx, ayah in enumerate(surah.get("ayahs", [])):
        normalized = normalize_text(ayah["ar"])
        
        ayah_data = {
            "ar": ayah["ar"],
            "en": ayah.get("en", ""),
            "fr": ayah.get("fr", ""),
            "nl": ayah.get("nl", ""),
            "normalized": normalized,
            "surah": surah_num,
            "ayah": ayah_idx + 1,
            "length": len(normalized)
        }
        all_ayahs.append(ayah_data)
        surah_lookup[surah_num].append(ayah_data)
        
        # Create normalized index for O(1) lookups
        if normalized not in normalized_index:
            normalized_index[normalized] = ayah_data

load_time = time.time() - start_load
print(f"[LOADING] Complete in {load_time:.2f}s")
print(f"[LOADED] {len(all_ayahs)} verses from Quran")

# ===============================
# Translation Cache
# ===============================
class TranslationCache:
    """كاش الترجمات لتسريع الجلب"""
    
    def __init__(self):
        self.cache = {}
        self.hit_count = 0
        self.miss_count = 0
    
    def get_translations(self, ayah_data: Dict, languages: List[str] = None) -> Dict:
        """احصل على الترجمات بسرعة"""
        if languages is None:
            languages = ['en', 'fr', 'nl']
        
        key = f"{ayah_data['surah']}:{ayah_data['ayah']}"
        
        if key in self.cache:
            self.hit_count += 1
            return self.cache[key]
        
        self.miss_count += 1
        result = {}
        for lang in languages:
            result[lang] = ayah_data.get(lang, "")
        
        self.cache[key] = result
        return result
    
    def get_stats(self) -> Dict:
        """احصائيات الكاش"""
        total = self.hit_count + self.miss_count or 1
        return {
            "cache_size": len(self.cache),
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": round(100 * self.hit_count / total, 1)
        }

translation_cache = TranslationCache()

# ===============================
# Global Matcher (from surah_detector)
# ===============================
from surah_detector import OptimizedRecitationMatcher, SURAH_NAMES

matcher = OptimizedRecitationMatcher()

# ===============================
# Optimized Search Functions
# ===============================

def find_matching_ayah_global(text: str, threshold: float = 0.40) -> Tuple[Optional[Dict], float]:
    """
    البحث العام المحسّن في كل المصحف
    مع تحسينات الأداء:
    1. Exact match (O(1))
    2. Length filtering (O(n/10))
    3. Early termination (O(n/100))
    """
    normalized = normalize_text(text)
    if not normalized:
        return None, 0
    
    # OPTIMIZATION 1: Exact match (instant!)
    if normalized in normalized_index:
        return normalized_index[normalized], 1.0
    
    text_len = len(normalized)
    best_match = None
    best_score = 0
    
    # OPTIMIZATION 2: Length-based filtering
    length_tolerance = max(int(text_len * 0.3), 5)
    min_len = max(1, text_len - length_tolerance)
    max_len = text_len + length_tolerance
    
    candidates = [
        ayah for ayah in all_ayahs
        if min_len <= ayah["length"] <= max_len
    ]
    
    print(f"[SEARCH] Filtered from {len(all_ayahs)} to {len(candidates)} candidates")
    
    # OPTIMIZATION 3: Early termination
    for ayah in candidates:
        score = similarity(normalized, ayah["normalized"])
        if score > 0.95:  # Very high confidence
            return ayah, score
        if score > best_score:
            best_score = score
            best_match = ayah
    
    if best_score > threshold:
        return best_match, best_score
    
    return None, best_score

# ===============================
# Main Processing Functions
# ===============================

def process_recognized_text(text: str) -> Dict:
    """
    معالجة النص المعترف به مع التحسينات
    """
    start_time = time.time()
    
    print(f"\n[DEBUG] Processing: {text}")
    
    # Use sequential prediction system
    result = matcher.process_recognized_text(text)
    
    # If sequential matching didn't work, fall back to global search
    if result["status"] == "no_match":
        print("[FALLBACK] Sequential matching failed, trying global search...")
        ayah, score = find_matching_ayah_global(text)
        if ayah:
            result["matched_ayah"] = ayah
            result["confidence"] = round(score, 2)
            result["status"] = "global_match"
            print(f"[FALLBACK] Global match in Surah {ayah['surah']}")
    
    # OPTIMIZATION: Get translations from cache
    if result["status"] != "no_match" and result.get("matched_ayah"):
        ayah = result["matched_ayah"]
        translations = translation_cache.get_translations(ayah)
        result["matched_ayah"]["translations"] = translations
        
        print(f"[MATCH] Found: {ayah['ar'][:50]}...")
        print(f"[CACHE] Hit rate: {translation_cache.get_stats()['hit_rate']}%")
    
    if result.get("predicted_next"):
        ayah = result["predicted_next"]
        translations = translation_cache.get_translations(ayah)
        result["predicted_next"]["translations"] = translations
        print(f"[PREDICTION] Next: {ayah['ar'][:50]}...")
    
    elapsed = (time.time() - start_time) * 1000
    print(f"[PERF] Total processing: {elapsed:.1f}ms")
    
    return result

def detect_surah_and_setup(text: str) -> Tuple[Optional[str], str]:
    """كشف السورة وإعداد النظام"""
    from surah_detector import detect_surah
    surah_num, method = detect_surah(text)
    
    if surah_num:
        matcher.predictor.set_surah(surah_num)
        print(f"[SETUP] Surah detected: {SURAH_NAMES.get(surah_num, {}).get('ar', surah_num)}")
    
    return surah_num, method

def on_ruku():
    """عند الركوع - إعادة تهيئة"""
    matcher.on_ruku()

def get_current_surah() -> Optional[str]:
    """احصل على السورة الحالية"""
    return matcher.predictor.current_surah

def get_consecutive_matches_count() -> int:
    """احصل على عدد التطابقات المتتالية"""
    return matcher.consecutive_matches

# ===============================
# Utility Functions
# ===============================

def batch_find_matches(texts: List[str]) -> List[Dict]:
    """طابق قائمة من النصوص (للاختبار)"""
    return [process_recognized_text(text) for text in texts]

def get_surah_verses(surah_num: str) -> List[Dict]:
    """احصل على كل آيات السورة"""
    return surah_lookup.get(surah_num, [])

def get_ayah_by_location(surah_num: str, ayah_num: int) -> Optional[Dict]:
    """احصل على آية محددة مع الترجمات"""
    verses = surah_lookup.get(surah_num, [])
    if ayah_num <= len(verses):
        ayah = verses[ayah_num - 1]
        ayah["translations"] = translation_cache.get_translations(ayah)
        return ayah
    return None

def get_ayah_translations(surah_num: str, ayah_num: int, languages: List[str] = None) -> Dict:
    """احصل على ترجمات آية محددة فقط (سريع!)"""
    ayah = get_ayah_by_location(surah_num, ayah_num)
    if ayah:
        return translation_cache.get_translations(ayah, languages)
    return {}

# ===============================
# Performance Monitoring
# ===============================

class PerformanceMonitor:
    """مراقبة الأداء"""
    
    def __init__(self):
        self.metrics = {
            "total_matches": 0,
            "sequential_matches": 0,
            "global_matches": 0,
            "failed_matches": 0,
            "avg_response_time": 0,
            "total_response_time": 0
        }
    
    def record_match(self, result: Dict, response_time_ms: float):
        """تسجيل نتيجة المطابقة"""
        self.metrics["total_matches"] += 1
        self.metrics["total_response_time"] += response_time_ms
        
        if result["status"] == "sequential_match":
            self.metrics["sequential_matches"] += 1
        elif result["status"] == "global_match":
            self.metrics["global_matches"] += 1
        else:
            self.metrics["failed_matches"] += 1
        
        self.metrics["avg_response_time"] = (
            self.metrics["total_response_time"] / self.metrics["total_matches"]
        )
    
    def get_stats(self) -> Dict:
        """احصائيات الأداء"""
        total = self.metrics["total_matches"] or 1
        return {
            "total_matches": self.metrics["total_matches"],
            "sequential_percentage": round(100 * self.metrics["sequential_matches"] / total, 1),
            "global_percentage": round(100 * self.metrics["global_matches"] / total, 1),
            "success_rate": round(100 * (total - self.metrics["failed_matches"]) / total, 1),
            "avg_response_time_ms": round(self.metrics["avg_response_time"], 1),
            "cache_hit_rate": translation_cache.get_stats()["hit_rate"]
        }
    
    def print_stats(self):
        """طباعة الإحصائيات"""
        stats = self.get_stats()
        print("\n[STATISTICS]")
        print(f"Total matches: {stats['total_matches']}")
        print(f"Sequential: {stats['sequential_percentage']}%")
        print(f"Global: {stats['global_percentage']}%")
        print(f"Success rate: {stats['success_rate']}%")
        print(f"Avg response: {stats['avg_response_time_ms']}ms")
        print(f"Cache hit rate: {stats['cache_hit_rate']}%")

# Create global performance monitor
performance_monitor = PerformanceMonitor()

print("[MATCHER] Initialized with sequential prediction system + caching")
print(f"[MATCHER] Loaded {len(all_ayahs)} verses from Quran")
print(f"[CACHE] Translation cache ready")
print(f"[INDEX] Normalized index ready for O(1) lookups")
