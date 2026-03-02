#!/usr/bin/env python3
"""
📖 Quran.json Auto Downloader
تحميل ملف القرآن الكامل تلقائياً
"""

import json
import urllib.request
import urllib.error
import os
import sys
from pathlib import Path

def ensure_data_dir():
    """التأكد من وجود مجلد data"""
    Path("data").mkdir(exist_ok=True)
    print("✓ Ensured data/ directory exists")

def download_from_github():
    """تحميل من GitHub"""
    print("\n📥 Downloading from GitHub...")
    
    urls = [
        "https://raw.githubusercontent.com/rn0x/quran-json/master/quran.json",
        "https://cdn.jsdelivr.net/gh/rn0x/quran-json@master/quran.json",
        "https://github.com/rn0x/quran-json/raw/master/quran.json"
    ]
    
    for url in urls:
        try:
            print(f"   Trying: {url}")
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                # تحقق من أن البيانات كاملة
                if isinstance(data, dict) and len(data) >= 100:
                    return data, url
                    
        except urllib.error.HTTPError as e:
            print(f"   ✗ HTTP Error {e.code}")
        except urllib.error.URLError as e:
            print(f"   ✗ URL Error: {e.reason}")
        except json.JSONDecodeError:
            print(f"   ✗ Invalid JSON")
        except Exception as e:
            print(f"   ✗ Error: {e}")
    
    return None, None

def verify_quran_data(data):
    """التحقق من صحة البيانات"""
    if not isinstance(data, dict):
        return False, "Data is not a dictionary"
    
    if len(data) < 110:  # يجب أن يكون 114 سورة
        return False, f"Only {len(data)} surahs (need 114)"
    
    total_ayahs = 0
    for surah_num, surah in data.items():
        if isinstance(surah, dict) and 'ayahs' in surah:
            ayahs = surah['ayahs']
            if isinstance(ayahs, list):
                total_ayahs += len(ayahs)
    
    if total_ayahs < 6000:  # يجب أن يكون ~6236
        return False, f"Only {total_ayahs} ayahs (need 6236)"
    
    return True, f"{len(data)} Surahs, {total_ayahs} Ayahs"

def save_quran_json(data, filename="data/quran.json"):
    """حفظ البيانات في ملف"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"✗ Error saving file: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("📖 QURAN.JSON AUTO DOWNLOADER")
    print("="*70)
    
    # تحقق من الملف الموجود
    if os.path.exists("data/quran.json"):
        print("\n📊 Checking existing quran.json...")
        try:
            with open("data/quran.json", 'r', encoding='utf-8') as f:
                existing = json.load(f)
                is_valid, msg = verify_quran_data(existing)
                
                if is_valid:
                    print(f"✅ Existing file is valid: {msg}")
                    return True
                else:
                    print(f"⚠️  Existing file is incomplete: {msg}")
                    print("   Will download complete version...")
        except:
            print("⚠️  Existing file is corrupted, will re-download...")
    
    # تحميل من مصادر متعددة
    ensure_data_dir()
    
    data, url = download_from_github()
    
    if data is None:
        print("\n❌ Failed to download from all sources!")
        print("\n📝 Please download manually from:")
        print("   https://github.com/rn0x/quran-json")
        print("\n   Or use:")
        print("   - https://quran-api.pages.dev/data/quran.json")
        print("   - https://cdn.jsdelivr.net/gh/rn0x/quran-json@master/quran.json")
        return False
    
    # التحقق من البيانات
    is_valid, msg = verify_quran_data(data)
    
    if not is_valid:
        print(f"\n❌ Downloaded data is invalid: {msg}")
        return False
    
    print(f"\n✅ Downloaded successfully from:\n   {url}")
    print(f"✅ Data is valid: {msg}")
    
    # حفظ الملف
    print("\n💾 Saving file...")
    if save_quran_json(data):
        print("✅ Saved to: data/quran.json")
        
        # إعادة التحقق
        with open("data/quran.json", 'r', encoding='utf-8') as f:
            saved = json.load(f)
            is_valid, msg = verify_quran_data(saved)
            print(f"✅ Verification: {msg}")
        
        print("\n" + "="*70)
        print("✨ SUCCESS! quran.json is ready!")
        print("="*70)
        print("\n🚀 Next step: python app.py\n")
        return True
    else:
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
