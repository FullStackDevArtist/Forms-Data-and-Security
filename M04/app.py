from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

app = Flask(__name__)

# SQLite database in the project folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///books.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)

# ------------ Model ------------
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_name = db.Column(db.String(120), nullable=False)
    author = db.Column(db.String(120), nullable=False)
    publisher = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f"<Book {self.id} {self.book_name!r}>"

# ------------ Schema ------------
class BookSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Book
        load_instance = True

book_schema = BookSchema()
books_schema = BookSchema(many=True)

# ------------ Routes ------------

# health check
@app.get("/ping")
def ping():
    return {"status": "ok"}

# Create a book
@app.post("/books")
def create_book():
    data = request.get_json(silent=True)
    if not data:
        abort(400, description="Request must be JSON.")
    required = ["book_name", "author", "publisher"]
    if any(k not in data or not data[k] for k in required):
        abort(400, description=f"Missing required fields: {required}")
    book = Book(
        book_name=data["book_name"],
        author=data["author"],
        publisher=data["publisher"],
    )
    db.session.add(book)
    db.session.commit()
    return book_schema.jsonify(book), 201

# Read all books
@app.get("/books")
def get_books():
    all_books = Book.query.all()
    return books_schema.jsonify(all_books)

# Read one book
@app.get("/books/<int:book_id>")
def get_book(book_id):
    book = Book.query.get_or_404(book_id)
    return book_schema.jsonify(book)

# Update a book (PUT = full update; PATCH = partial update)
@app.route("/books/<int:book_id>", methods=["PUT", "PATCH"])
def update_book(book_id):
    book = Book.query.get_or_404(book_id)
    data = request.get_json(silent=True) or {}
    # For PUT, ensure all fields exist; for PATCH, update only provided ones.
    if request.method == "PUT":
        for k in ["book_name", "author", "publisher"]:
            if k not in data or not data[k]:
                abort(400, description=f"PUT requires all fields: book_name, author, publisher")
    if "book_name" in data:
        book.book_name = data["book_name"]
    if "author" in data:
        book.author = data["author"]
    if "publisher" in data:
        book.publisher = data["publisher"]
    db.session.commit()
    return book_schema.jsonify(book)

# Delete a book
@app.delete("/books/<int:book_id>")
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    return {"message": f"Book {book_id} deleted."}, 200

# Convenience: allow 'python app.py' to run the server too
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
