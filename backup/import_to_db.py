# import_to_db.py
import re
import configparser
import os
from database import Database, DB_CONFIG # 假设 database 模块和 DB_CONFIG 存在且可用

# --- 配置加载 ---
config = configparser.ConfigParser()
script_dir = os.path.dirname(__file__)
config_path = os.path.join(script_dir, 'config.ini')

try:
    config.read(config_path)
    # 从配置文件中读取核心书卷信息
    BOOK_NAME_CHINESE = config['BookInfo']['BOOK_NAME_CHINESE']
    BOOK_NAME_ENGLISH = config['BookInfo']['BOOK_NAME_ENGLISH']

    # 自动生成清洗后的文件名和数据库中的书卷名
    CLEANED_FILE = f"{BOOK_NAME_ENGLISH}_clean.txt"
    BOOK_NAME = BOOK_NAME_CHINESE # 数据库中的书卷名通常是中文名

except KeyError as e:
    print(f"错误: 配置文件中缺少必要的键 '{e}'。请检查 config.ini 文件。")
    exit(1)
except FileNotFoundError:
    print(f"错误: 未找到配置文件 '{config_path}'。请确保文件存在。")
    exit(1)
except Exception as e:
    print(f"读取配置文件时发生错误: {e}")
    exit(1)

# ===================================================================
# == 无需再修改这里，参数已从 config.ini 读取并自动生成
# ===================================================================


def parse_cleaned_data(file_path, book_name):
    """
    解析清洗后的文本文件以提取经文数据。
    """
    verses_to_insert = []
    current_chapter = 0

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                line = line.strip()
                if not line:
                    continue

                chapter_header_match = re.match(r'Chapter_Header:\s*(\d+)', line)
                if chapter_header_match:
                    current_chapter = int(chapter_header_match.group(1))
                    print(f"正在解析 {book_name} 第 {current_chapter} 章...")
                    continue

                verse_content_match = re.match(r'Verse_Ch:\s*(\d+):(\d+)\s*(.*)###EN###\s*(.*)', line)
                if verse_content_match:
                    chapter_num, verse_num = int(verse_content_match.group(1)), int(verse_content_match.group(2))
                    chinese_content = verse_content_match.group(3).strip()
                    english_content = verse_content_match.group(4).strip()

                    combined_content = f"{chinese_content}\n{english_content}"

                    if chapter_num != current_chapter:
                        print(f"警告: 章节号不匹配。应为 {current_chapter}, 找到 {chapter_num}。跳过行: {line}")
                        continue

                    verses_to_insert.append((book_name, current_chapter, verse_num, combined_content))
    except FileNotFoundError:
        print(f"错误: 未找到清洗后的文件 '{file_path}'。")
        return None
    return verses_to_insert


def import_verses_to_db(verses_data, book_name):
    """
    将解析出的经文数据导入数据库。
    """
    if not verses_data:
        print(f"没有为《{book_name}》解析出任何经文。中止导入。")
        return

    db = Database(**DB_CONFIG)
    db.connect()
    if not db.connection:
        return

    # 1. 获取 book_id
    book_info = db.fetch_one("SELECT id FROM books WHERE name = %s", (book_name,))
    if not book_info:
        print(f"错误: 在 'books' 表中未找到《{book_name}》。请先插入该书卷的信息。")
        db.close()
        return
    book_id = book_info['id']

    # 2. 清理该书卷的旧经文
    print(f"正在清理《{book_name}》(book_id={book_id}) 的旧经文...")
    db.execute_query("DELETE FROM verses WHERE book_id = %s", (book_id,))
    print("旧经文已清理。")

    # 3. 批量插入新经文
    sql_insert = "INSERT INTO verses (book_id, chapter, verse_number, content) VALUES (%s, %s, %s, %s)"
    data_to_insert = [(book_id, v[1], v[2], v[3]) for v in verses_data]

    if db.executemany_query(sql_insert, data_to_insert):
        print(f"成功为《{book_name}》插入 {len(data_to_insert)} 条经文。")
    else:
        print(f"为《{book_name}》插入经文失败。")
        db.close()
        return

    # 4. 更新总章节数
    max_chapter_query = db.fetch_one("SELECT MAX(chapter) as max_chap FROM verses WHERE book_id = %s", (book_id,))
    max_chapter = max_chapter_query['max_chap'] if max_chapter_query and max_chapter_query['max_chap'] else 0
    db.execute_query("UPDATE books SET total_chapters = %s WHERE id = %s", (max_chapter, book_id))
    print(f"已将《{book_name}》的总章节数更新为: {max_chapter}。")

    db.close()


if __name__ == "__main__":
    parsed_data = parse_cleaned_data(CLEANED_FILE, BOOK_NAME)
    if parsed_data:
        import_verses_to_db(parsed_data, BOOK_NAME)