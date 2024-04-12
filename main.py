from fastapi import FastAPI, Depends, HTTPException
from fastapi_pagination import paginate, add_pagination, Page
from sqlalchemy.orm import Session

import crud
import pagination
import schemas
from database import SessionLocal
from models import Book

app = FastAPI()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/books/", response_model=Page[pagination.BookOut])
def get_books_list(
        author_id: int | None = None,
        db: Session = Depends(get_db)
):
    return paginate(crud.get_books(author_id, db))


def get_book_by_title(title: str, db: Session = Depends(get_db)):
    return (
        db.query(Book)
        .filter(Book.title == title)
        .first()
    )


@app.post("/books/", response_model=schemas.BookRead)
def create_book(book: schemas.BookCreate, db: Session = Depends(get_db)):
    if get_book_by_title(book.title, db):
        raise HTTPException(
            status_code=400,
            detail="Book with that title already exists",
        )

    return crud.create_book(db, book)


@app.get("/authors/", response_model=Page[pagination.AuthorOut])
def get_authors_list(db: Session = Depends(get_db)):
    return paginate(crud.get_authors(db))


@app.get("/authors/{author_id}/", response_model=schemas.AuthorReadDetail)
def get_author_detail(author_id: int, db: Session = Depends(get_db)):
    if author := crud.get_author_by_id(db, author_id):
        return author

    raise HTTPException(
        status_code=404,
        detail="Author not found",
    )


@app.post(
    "/authors/{author_id}/create-book/",
    response_model=schemas.AuthorReadDetail
)
def create_book_for_author(
        author_id: int,
        book: schemas.BookAuthorCreate,
        db: Session = Depends(get_db)
):
    if author := crud.get_author_by_id(db, author_id):

        if get_book_by_title(book.title, db):
            raise HTTPException(
                status_code=400,
                detail="Book with that title already exists",
            )

        book_data = book.dict()
        book_data["author_id"] = author_id
        book = schemas.BookCreate(**book_data)

        crud.create_book(db, book)
        return author

    raise HTTPException(status_code=404, detail="Author not found")


add_pagination(app)
