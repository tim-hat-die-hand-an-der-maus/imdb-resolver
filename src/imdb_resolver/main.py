import logging
import os
import re
from typing import Annotated, Self

import sentry_sdk
from fastapi import FastAPI, HTTPException
from imdb import Cinemagoer
from imdb.helpers import get_byURL
from imdb.Movie import Movie
from pydantic import BaseModel, Field, HttpUrl

_logger = logging.getLogger(__name__)

COVER_URL_SIZE_REGEX = r"._V\d+_\w+\d+_\w+\d+,\d+,(\d+),(\d+)_"


def _basic_setup() -> None:
    logging.basicConfig()
    logging.getLogger(__package__).setLevel(logging.DEBUG)
    dsn = os.getenv("SENTRY_DSN")
    if dsn:
        sentry_sdk.init(
            dsn=dsn,
            release=os.getenv("APP_VERSION", "dev"),
        )
    else:
        _logger.warning("Sentry is disabled")


def remove_size_from_cover_url(url: str) -> str:
    return re.sub(COVER_URL_SIZE_REGEX, "", url)


def get_ratio_from_cover_url(url: str) -> float:
    if matches := re.findall(COVER_URL_SIZE_REGEX, url):
        width, height = matches[0]

        return int(height) / int(width)

    raise ValueError("Could not determine ratio of cover")


class ResolverRequest(BaseModel):
    imdbUrl: str


class SearchRequest(BaseModel):
    title: str


class CoverMetadataResponse(BaseModel):
    url: str
    ratio: float


class MovieResponse(BaseModel):
    id: str
    title: str
    year: int
    rating: str
    cover: CoverMetadataResponse
    imdb_url: Annotated[HttpUrl, Field(serialization_alias="imdbUrl")]

    @classmethod
    def from_imdb_movie(cls, movie: Movie) -> Self | None:
        cover_url = movie.data.get("cover url")
        if not cover_url:
            _logger.warning("Ignoring movie with missing cover url")
            return None
        cover_ratio = get_ratio_from_cover_url(cover_url)
        cover_url = remove_size_from_cover_url(cover_url)

        return cls(
            id=movie.movieID,
            title=movie.data["title"],
            year=movie.data.get("year"),
            rating=str(movie.data.get("rating")),
            cover=CoverMetadataResponse(url=cover_url, ratio=cover_ratio),
            imdb_url=f"https://www.imdb.com/title/tt{movie.movieID}",  # type: ignore
        )


_basic_setup()
app = FastAPI()


@app.post("/search")
def search(req: SearchRequest):
    imdb = Cinemagoer()

    results = []
    for movie in imdb.search_movie(req.title):
        response = MovieResponse.from_imdb_movie(movie)
        if response is not None:
            results.append(response.model_dump())

    return {"results": results}


def resolve_link(url: str) -> MovieResponse | None:
    movie = get_byURL(url)

    if not movie:
        match = re.search(r".*tt(\d+)", url)

        if match:
            imdb_id = match.group(1)
            movie = Cinemagoer().get_movie(imdb_id)

    if movie:
        return MovieResponse.from_imdb_movie(movie)
    else:
        return None


@app.post("/")
def movie_by_link(req: ResolverRequest):
    movie = resolve_link(req.imdbUrl)

    if not movie:
        raise HTTPException(
            status_code=404,
            detail=f"link (`{req.imdbUrl}`) couldn't be resolved to a movie",
        )
    else:
        return movie
