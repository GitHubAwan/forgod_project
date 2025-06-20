# split_bible_books.py
import re
import os


def split_bible_books(input_file_path, output_dir="raw_books"):
    """
    将圣经文本文件按书卷分割成独立的TXT文件。

    Args:
        input_file_path (str): 包含所有书卷的原始文本文件路径。
        output_dir (str): 保存分割后书卷的目录。如果不存在，将创建该目录。
    """

    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"已创建输出目录: {output_dir}")

    # 匹配书卷标题的正则表达式。
    # 示例: "32. 约拿书 Jonah" 或 "40. 马太福音 Matthew"
    # 捕获中文书名和英文书名
    # 注意：这里假设章节标题行不会包含类似 "872" 这样的行号干扰
    book_header_pattern=re.compile(r'^\d+\.\s*(.*?)\s+([a-zA-Z0-9\s\-\.]+)\s*$')

    current_book_name_english=None
    current_book_content=[]
    total_books_split=0

    try:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line=line.strip()

                # 检查是否是新的书卷标题行
                match=book_header_pattern.match(line)
                if match:
                    # 获取当前书卷的英文名作为文件名
                    new_book_name_chinese=match.group(1).strip()
                    new_book_name_english=match.group(2).replace(' ', '_').strip()  # 将空格替换为下划线，适应文件名

                    if current_book_name_english:
                        # 保存上一本书的内容
                        output_file_name=os.path.join(output_dir, f"{current_book_name_english}_raw.txt")
                        if current_book_content:  # 确保内容不为空才写入
                            with open(output_file_name, 'w', encoding='utf-8') as outfile:
                                outfile.write("\n".join(current_book_content).strip())  # 去除开头和结尾的空行
                            print(f"已保存书卷: '{new_book_name_chinese}' 为 '{output_file_name}'")
                            total_books_split+=1
                        else:
                            print(f"警告: 书卷 '{new_book_name_chinese}' (前一卷) 内容为空，未保存。")

                    # 重置为新的书卷
                    current_book_name_english=new_book_name_english
                    current_book_content=[]
                    # 首次匹配到的书卷标题本身不应该作为正文内容，但由于您的约拿书第一行是标题，第二行才是正文。
                    # 为了包含 "约拿书 Jonah 第 1 章" 这样的章节头，我们将标题行也加入到内容中
                    current_book_content.append(line)
                    continue

                # 如果不是书卷标题行，且已经有当前书卷名（即已经识别到第一本书），则添加到当前书卷内容
                if current_book_name_english:
                    # 检查是否是章节行号（如 "872"），如果是则跳过
                    if re.fullmatch(r'\d{1,4}', line):  # 假设行号最多4位
                        continue
                    current_book_content.append(line)
                # else:
                #    # 如果在第一本书标题之前有内容，这部分内容会被忽略，通常是文件头信息
                #    if line.strip():
                #        print(f"WARN: Skipping pre-book content at line {line_num}: {line.strip()}")

        # 文件读取完毕，保存最后一个书卷的内容
        if current_book_name_english and current_book_content:
            output_file_name=os.path.join(output_dir, f"{current_book_name_english}_raw.txt")
            with open(output_file_name, 'w', encoding='utf-8') as outfile:
                outfile.write("\n".join(current_book_content).strip())
            print(f"已保存书卷: '{current_book_name_english}' (最后一卷) 为 '{output_file_name}'")
            total_books_split+=1
        else:
            print("文件内容未识别到任何书卷，或文件为空。")

    except FileNotFoundError:
        print(f"错误: 未找到输入文件 '{input_file_path}'。请检查路径。")
    except Exception as e:
        print(f"处理文件时发生意外错误: {e}")

    print(f"\n分割完成。共分割 {total_books_split} 个书卷。")


if __name__ == "__main__":
    # 请将 '圣经部分.txt' 替换为您实际的文件名
    input_bible_file="圣经部分.txt"
    # 指定输出目录，所有分割后的文件会保存在这里
    output_directory="bible_raw_books"

    split_bible_books(input_bible_file, output_directory)
    print(f"\n所有分割后的文件已保存到 '{output_directory}' 目录。")