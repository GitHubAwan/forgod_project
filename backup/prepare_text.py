# prepare_text.py
import re
import configparser
import os

# --- 配置加载 ---
config = configparser.ConfigParser()
script_dir = os.path.dirname(__file__)
config_path = os.path.join(script_dir, 'config.ini')

try:
    config.read(config_path)
    # 从配置文件中读取核心书卷信息
    BOOK_NAME_CHINESE = config['BookInfo']['BOOK_NAME_CHINESE']
    BOOK_NAME_ENGLISH = config['BookInfo']['BOOK_NAME_ENGLISH']

    # 根据英文书名自动生成文件名
    RAW_INPUT_FILE = f"{BOOK_NAME_ENGLISH}_raw.txt"
    CLEAN_OUTPUT_FILE = f"{BOOK_NAME_ENGLISH}_clean.txt"

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


def clean_text_generic(raw_text_content, book_name_chinese, book_name_english):
    """
    通用的圣经文本清洗逻辑。
    通过参数接收书卷名，能正确处理跨越多行的中英文经文。
    """
    lines = raw_text_content.split('\n')

    output_blocks = []
    current_block = None

    # 根据传入的变量构造动态的正则表达式
    # chapter_pattern = re.compile(rf'{book_name_chinese}\s+{book_name_english}\s+第\s*(\d+)\s*章')
    chapter_pattern=re.compile(rf'{book_name_chinese}\s+{book_name_english}\s+第\s*(\d+)\s*(章|篇)')
    title_pattern = re.compile(rf'^\d+\.\s*{book_name_chinese}\s+{book_name_english}')

    for line in lines:
        line = line.strip()

        if not line or re.fullmatch(r'\d{1,3}', line):
            continue

        chapter_match = chapter_pattern.match(line)
        if chapter_match:
            if current_block:
                output_blocks.append(current_block)
            current_block = None
            output_blocks.append(f"Chapter_Header: {chapter_match.group(1)}")
            continue

        verse_match = re.match(r'(\d+):(\d+)\s*(.*)', line)
        if verse_match:
            if current_block:
                output_blocks.append(current_block)

            current_block = {
                "chapter": verse_match.group(1),
                "verse": verse_match.group(2),
                "content": [verse_match.group(3).strip()]
            }
        elif current_block:
            current_block["content"].append(line)
        else:
            if not title_pattern.match(line):
                print(f"WARN: Skipping unassociated line: {line}")

    if current_block:
        output_blocks.append(current_block)

    formatted_lines = []
    for block in output_blocks:
        if isinstance(block, str):
            formatted_lines.append(block)
            continue

        full_content_str = " ".join(block["content"])
        first_letter_match = re.search(r'[a-zA-Z]', full_content_str)

        if first_letter_match:
            split_index = first_letter_match.start()
            chinese_part = re.sub(r'\s+', ' ', full_content_str[:split_index].strip())
            english_part = re.sub(r'\s+', ' ', full_content_str[split_index:].strip())

            formatted_lines.append(
                f"Verse_Ch: {block['chapter']}:{block['verse']} {chinese_part} ###EN### {english_part}"
            )
        else:
            formatted_lines.append(
                f"Verse_Ch: {block['chapter']}:{block['verse']} {full_content_str.strip()}"
            )

    return "\n".join(formatted_lines)


if __name__ == "__main__":
    try:
        with open(RAW_INPUT_FILE, 'r', encoding='utf-8') as f:
            raw_content = f.read()

        cleaned_content = clean_text_generic(raw_content, BOOK_NAME_CHINESE, BOOK_NAME_ENGLISH)

        if cleaned_content:
            with open(CLEAN_OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write(cleaned_content)
            print(f"\n成功: 已清洗 '{RAW_INPUT_FILE}' 并保存至 '{CLEAN_OUTPUT_FILE}'.")
        else:
            print("错误: 清洗过程未能生成内容。")
    except FileNotFoundError:
        print(f"错误: 未找到原始输入文件 '{RAW_INPUT_FILE}'。请检查文件名和路径。")
    except Exception as e:
        print(f"发生意外错误: {e}")