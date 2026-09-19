from flask import Flask, render_template, request, redirect, abort
from database import get_db, init_db
from werkzeug.utils import secure_filename
import os
import re

app = Flask(__name__)

init_db()


# --------------------------------
# IMAGE UPLOAD SETTINGS
# --------------------------------

UPLOAD_FOLDER = os.path.join(
    app.root_path,
    "static",
    "images"
)

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp"
}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# --------------------------------
# CREATE ARTICLE SLUG
# --------------------------------

def create_slug(title):

    slug = title.lower()

    slug = re.sub(
        r"[^a-z0-9\s-]",
        "",
        slug
    )

    slug = re.sub(
        r"\s+",
        "-",
        slug
    )

    return slug.strip("-")


# --------------------------------
# HOME PAGE
# --------------------------------

@app.route("/")
def home():

    db = get_db()

    articles = db.execute("""
        SELECT *
        FROM articles
        ORDER BY published_at DESC
    """).fetchall()

    db.close()

    return render_template(
        "index.html",
        articles=articles
    )


# --------------------------------
# CATEGORY PAGE
# --------------------------------

@app.route("/category/<category>")
def category(category):

    db = get_db()

    articles = db.execute("""
        SELECT *
        FROM articles
        WHERE LOWER(category) = LOWER(?)
        ORDER BY published_at DESC
    """, (category,)).fetchall()

    db.close()

    return render_template(
        "category.html",
        articles=articles,
        category=category
    )


# --------------------------------
# ADMIN PAGE
# --------------------------------

@app.route("/admin")
def admin():

    return render_template(
        "admin.html"
    )


# --------------------------------
# ADD ARTICLE
# --------------------------------

@app.route("/admin/add", methods=["POST"])
def add_article():

    title = request.form["title"]

    category = request.form["category"]

    author = request.form["author"]

    published_at = request.form["published_at"]

    source = request.form["source"]

    content = request.form["content"]


    # Create slug

    slug = create_slug(title)


    # --------------------------------
    # HANDLE IMAGE
    # --------------------------------

    image_filename = None

    image = request.files.get("image")


    if image and image.filename:

        if allowed_file(image.filename):

            image_filename = secure_filename(
                image.filename
            )

            image.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    image_filename
                )
            )

        else:

            abort(
                400,
                description="Invalid image format. Use PNG, JPG, JPEG, or WEBP."
            )


    # --------------------------------
    # SAVE ARTICLE
    # --------------------------------

    db = get_db()

    db.execute("""
        INSERT INTO articles
        (
            title,
            slug,
            content,
            category,
            author,
            published_at,
            image,
            source
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        title,
        slug,
        content,
        category,
        author,
        published_at,
        image_filename,
        source
    ))

    db.commit()

    db.close()


    return redirect("/")


# --------------------------------
# ARTICLE PAGE
# --------------------------------

@app.route("/article/<slug>")
def article(slug):

    db = get_db()

    article = db.execute("""
        SELECT *
        FROM articles
        WHERE slug = ?
    """, (slug,)).fetchone()

    db.close()


    if article is None:

        abort(404)


    return render_template(
        "article.html",
        article=article
    )


# --------------------------------
# START SERVER
# --------------------------------

if __name__ == "__main__":

    app.run(
        debug=True
    )