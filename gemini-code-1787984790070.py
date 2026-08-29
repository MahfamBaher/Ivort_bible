import os
import json
import sqlite3
import glob

# مسیر پوشه‌ها
JSON_DIR = "./"
OUTPUT_DIR = "./sqlite_files"

# ساخت پوشه خروجی در صورت عدم وجود
os.makedirs(OUTPUT_DIR, exist_ok=True)

def process_json_file(file_path):
    file_name = os.path.basename(file_path)
    sqlite_name = file_name.replace(".json", ".sqlite")
    db_path = os.path.join(OUTPUT_DIR, sqlite_name)
    
    print(f"\n⚙️ Processing: {file_name} ➡️ {sqlite_name}")
    
    # استفاده از utf-8-sig جهت حذف اتوماتیک کاراکتر BOM
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except Exception as e:
        print(f"   ❌ Error reading {file_path}: {e}")
        return

    # حذف فایل SQLite قبلی در صورت وجود جهت بازنویسی تمیز
    if os.path.exists(db_path):
        os.remove(db_path)
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # ساخت جدول آیکه‌ها (verses)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_abbrev TEXT,
            book_number INTEGER,
            chapter INTEGER,
            verse INTEGER,
            text TEXT
        )
    """)
    
    total_verses = 0
    
    # استخراج لیست کتاب‌ها بر اساس ساختار JSON (آرایه یا دیکشنری با کلید books)
    books_data = []
    if isinstance(data, list):
        books_data = data
    elif isinstance(data, dict):
        books_data = data.get("books", [])
    
    # پردازش کتاب‌ها
    for book_idx, book_data in enumerate(books_data, start=1):
        if not isinstance(book_data, dict):
            continue
        
        # دریافت نام یا اختصار کتاب
        abbrev = book_data.get("abbrev") or book_data.get("name", "")
        chapters = book_data.get("chapters", [])
        
        for ch_idx, chapter in enumerate(chapters, start=1):
            # ساختار اول: فصل به صورت آرایه‌ای از متون آیه‌ها است
            if isinstance(chapter, list):
                for v_idx, verse_text in enumerate(chapter, start=1):
                    cursor.execute(
                        "INSERT INTO verses (book_abbrev, book_number, chapter, verse, text) VALUES (?, ?, ?, ?, ?)",
                        (abbrev, book_idx, ch_idx, v_idx, str(verse_text))
                    )
                    total_verses += 1
            
            # ساختار دوم: فصل به صورت یک دیکشنری شامل شماره فصل و آرایه‌ای از آیه‌ها است
            elif isinstance(chapter, dict):
                current_chapter = chapter.get("chapter", ch_idx)
                verses = chapter.get("verses", [])
                
                for v_idx_default, verse_item in enumerate(verses, start=1):
                    if isinstance(verse_item, dict):
                        v_idx = verse_item.get("verse", v_idx_default)
                        v_text = verse_item.get("text", "")
                    else:
                        v_idx = v_idx_default
                        v_text = str(verse_item)
                        
                    cursor.execute(
                        "INSERT INTO verses (book_abbrev, book_number, chapter, verse, text) VALUES (?, ?, ?, ?, ?)",
                        (abbrev, book_idx, current_chapter, v_idx, str(v_text))
                    )
                    total_verses += 1

    # ایجاد ایندکس جهت افزایش سرعت جستجو در برنامه‌های موبایل (Flutter / Dart)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_book_ch_v ON verses(book_abbrev, chapter, verse)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_book_num ON verses(book_number, chapter, verse)")

    conn.commit()
    conn.close()
    
    print(f"   ✅ Successfully created '{sqlite_name}' with {total_verses} verses.")

def main():
    json_files = glob.glob(os.path.join(JSON_DIR, "*.json"))
    if not json_files:
        print(f"⚠️ No JSON files found in '{JSON_DIR}' directory.")
        return
        
    print(f"🚀 Engine started! Found {len(json_files)} JSON file(s) in '{JSON_DIR}'...")
    
    for file_path in json_files:
        process_json_file(file_path)
        
    print(f"\n🎉 All done! Engine processed {len(json_files)} file(s). Generated SQLite files are in '{OUTPUT_DIR}'.")

if __name__ == "__main__":
    main()