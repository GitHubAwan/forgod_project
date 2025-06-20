# app.py
#-*- coding: utf-8 -*-
from flask import Flask, render_template, jsonify, g
from database import Database, DB_CONFIG

app = Flask(__name__)
db_instance = Database(**DB_CONFIG)

@app.before_request
def before_request():
    g.db_conn = db_instance.connect()
    if not g.db_conn:
        pass

@app.teardown_request
def teardown_request(exception):
    db_conn = g.pop('db_conn', None)
    if db_conn:
        db_conn.close()

@app.route('/')
def index():
    old_testament_books = db_instance.fetch_all("SELECT id, name FROM books WHERE is_old_testament = 1 ORDER BY id")
    new_testament_books = db_instance.fetch_all("SELECT id, name FROM books WHERE is_old_testament = 0 ORDER BY id")
    print("\n--- Debugging Book Names from Flask Backend ---")
    if old_testament_books:
        for book in old_testament_books:
            print(f"Book ID: {book['id']}, Name: {book['name']}")
    else:
        print("No old testament books found.")
    if new_testament_books:
        for book in new_testament_books:
            print(f"Book ID: {book['id']}, Name: {book['name']}")
    else:
        print("No new testament books found.")
    print("---------------------------------------------\n")
    return render_template('index.html', old_testament=old_testament_books, new_testament=new_testament_books)

@app.route('/book/<int:book_id>')
def book(book_id):
    # 参数传入字典，使用 :id 占位符
    book_info = db_instance.fetch_one("SELECT id, name, total_chapters FROM books WHERE id = :id", {'id': book_id})
    if not book_info:
        return "Book not found", 404

    prev_book = db_instance.fetch_one("SELECT id, name FROM books WHERE id < :id ORDER BY id DESC LIMIT 1", {'id': book_id})
    next_book = db_instance.fetch_one("SELECT id, name FROM books WHERE id > :id ORDER BY id ASC LIMIT 1", {'id': book_id})

    chapters = list(range(1, book_info['total_chapters'] + 1))
    return render_template('book.html', book=book_info, chapters=chapters, prev_book=prev_book, next_book=next_book)

@app.route('/chapter/<int:book_id>/<int:chapter_number>')
def chapter(book_id, chapter_number):
    book_info = db_instance.fetch_one("SELECT id, name, total_chapters FROM books WHERE id = :id", {'id': book_id})
    if not book_info:
        return "Book not found", 404

    if not (1 <= chapter_number <= book_info['total_chapters']):
        return "Chapter not found", 404

    verses = db_instance.fetch_all(
        "SELECT verse_number, content FROM verses WHERE book_id = :book_id AND chapter = :chapter ORDER BY verse_number",
        {'book_id': book_id, 'chapter': chapter_number}
    )

    prev_chapter_book_id = book_id
    prev_chapter_number = chapter_number - 1
    if prev_chapter_number < 1:
        prev_book = db_instance.fetch_one("SELECT id, name, total_chapters FROM books WHERE id < :id ORDER BY id DESC LIMIT 1", {'id': book_id})
        if prev_book:
            prev_chapter_book_id = prev_book['id']
            prev_chapter_number = prev_book['total_chapters']
        else:
            prev_chapter_book_id = None

    next_chapter_book_id = book_id
    next_chapter_number = chapter_number + 1
    if next_chapter_number > book_info['total_chapters']:
        next_book = db_instance.fetch_one("SELECT id, name FROM books WHERE id > :id ORDER BY id ASC LIMIT 1", {'id': book_id})
        if next_book:
            next_chapter_book_id = next_book['id']
            next_chapter_number = 1
        else:
            next_chapter_book_id = None

    return render_template('chapter.html',
                           book=book_info,
                           chapter_number=chapter_number,
                           verses=verses,
                           prev_chapter_book_id=prev_chapter_book_id,
                           prev_chapter_number=prev_chapter_number,
                           next_chapter_book_id=next_chapter_book_id,
                           next_chapter_number=next_chapter_number)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=50001)