# clean_and_import_books.py

import pymysql
from database import DB_CONFIG  # 导入你的数据库配置

# 圣经书卷数据
OLD_TESTAMENT_BOOKS=[
    ('创世记', 50), ('出埃及记', 40), ('利未记', 27), ('民数记', 36), ('申命记', 34),
    ('约书亚记', 24), ('士师记', 21), ('路得记', 4), ('撒母耳记上', 31), ('撒母耳记下', 24),
    ('列王纪上', 22), ('列王纪下', 25), ('历代志上', 29), ('历代志下', 36), ('以斯拉记', 10),
    ('尼希米记', 13), ('以斯帖记', 10), ('约伯记', 42), ('诗篇', 150), ('箴言', 31),
    ('传道书', 12), ('雅歌', 8), ('以赛亚书', 66), ('耶利米书', 52), ('耶利米哀歌', 5),
    ('以西结书', 48), ('但以理书', 12), ('何西阿书', 14), ('约珥书', 3), ('阿摩司书', 9),
    ('俄巴底亚书', 1), ('约拿书', 4), ('弥迦书', 7), ('那鸿书', 3), ('哈巴谷书', 3),
    ('西番雅书', 3), ('哈该书', 2), ('撒迦利亚书', 14), ('玛拉基书', 4)
]

NEW_TESTAMENT_BOOKS=[
    ('马太福音', 28), ('马可福音', 16), ('路加福音', 24), ('约翰福音', 21), ('使徒行传', 28),
    ('罗马书', 16), ('哥林多前书', 16), ('哥林多后书', 13), ('加拉太书', 6), ('以弗所书', 6),
    ('腓立比书', 4), ('歌罗西书', 4), ('帖撒罗尼迦前书', 5), ('帖撒罗尼迦后书', 3),
    ('提摩太前书', 6), ('提摩太后书', 4), ('提多书', 3), ('腓利门书', 1),
    ('希伯来书', 13), ('雅各书', 5), ('彼得前书', 5), ('彼得后书', 3),
    ('约翰一书', 5), ('约翰二书', 1), ('约翰三书', 1), ('犹大书', 1), ('启示录', 22)
]


def clean_and_import():
    connection=None
    try:
        connection=pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['db'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            init_command="SET NAMES utf8mb4"  # 确保连接字符集
        )
        with connection.cursor() as cursor:
            # 禁用外键检查，以便清空表（如果有 verses 表的引用）
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

            # 清空 books 表
            cursor.execute("TRUNCATE TABLE books;")
            print("books 表已清空。")

            # 插入旧约书卷
            for name, total_chapters in OLD_TESTAMENT_BOOKS:
                cursor.execute(
                    "INSERT INTO books (name, is_old_testament, total_chapters) VALUES (%s, %s, %s)",
                    (name, True, total_chapters)
                )
            print(f"已插入 {len(OLD_TESTAMENT_BOOKS)} 条旧约书卷。")

            # 插入新约书卷
            for name, total_chapters in NEW_TESTAMENT_BOOKS:
                cursor.execute(
                    "INSERT INTO books (name, is_old_testament, total_chapters) VALUES (%s, %s, %s)",
                    (name, False, total_chapters)
                )
            print(f"已插入 {len(NEW_TESTAMENT_BOOKS)} 条新约书卷。")

            # 重新启用外键检查
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

            connection.commit()
            print("数据导入完成。")

    except pymysql.Error as e:
        print(f"数据库操作失败: {e}")
        if connection:
            connection.rollback()
    finally:
        if connection:
            connection.close()


if __name__ == '__main__':
    clean_and_import()