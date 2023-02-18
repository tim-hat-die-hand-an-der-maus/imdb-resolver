import re
from typing import Optional

from fastapi import HTTPException, FastAPI
from imdb import Cinemagoer
from imdb.Movie import Movie
from imdb.helpers import get_byURL
from pydantic import BaseModel

COVER_URL_SIZE_REGEX = r"._V\d+_\w+\d+_\w+\d+,\d+,(\d+),(\d+)_"


def remove_size_from_cover_url(url: str) -> str:
    return re.sub(COVER_URL_SIZE_REGEX, "", url)


def get_ratio_from_cover_url(url: str) -> float:
    if matches := re.findall(COVER_URL_SIZE_REGEX, url):
        width, height = matches[0]

        return int(height) / int(width)


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
    coverUrl: str

    @classmethod
    def from_imdb_movie(cls, movie: Movie):
        cover_url = movie.data["cover url"]
        cover_ratio = get_ratio_from_cover_url(cover_url)
        cover_url = remove_size_from_cover_url(cover_url)

        return cls(
            id=movie.movieID,
            title=movie.data['title'],
            year=movie.data.get('year'),
            rating=str(movie.data.get('rating')),
            cover=CoverMetadataResponse(url=cover_url, ratio=cover_ratio),
            coverUrl=cover_url,
        )


app = FastAPI()


@app.post("/search")
def search(req: SearchRequest):
    imdb = Cinemagoer()

    return {
        "results": [MovieResponse.from_imdb_movie(movie).dict() for movie in imdb.search_movie(req.title)]
    }


def resolve_link(url: str) -> Optional[MovieResponse]:
    movie = get_byURL(url)

    if not movie:
        match = re.search(r".*tt(\d+)", url)

        if match:
            imdb_id = match.group(1)
            return Cinemagoer().get_movie(imdb_id)

    return None


@app.post("/")
def movie_by_link(req: ResolverRequest):
    movie = resolve_link(req.imdbUrl)

    if not movie:
        raise HTTPException(status_code=404, detail=f"link (`{req.imdbUrl}`) couldn't be resolved to a movie")
    else:
        return movie
