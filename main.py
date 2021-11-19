from fastapi import FastAPI, HTTPException
from imdb import IMDb
from imdb.Movie import Movie
from imdb.helpers import get_byURL
from pydantic import BaseModel

import re


class ResolverRequest(BaseModel):
    imdbUrl: str


app = FastAPI()


COVER_URL_SIZE_REGEX = r"._V\d+_\w+\d+_\w+\d+,\d+,(\d+),(\d+)_"


def remove_size_from_cover_url(url: str) -> str:
    return re.sub(COVER_URL_SIZE_REGEX, "", url)


def get_ratio_from_cover_url(url: str) -> float:
    if matches := re.findall(COVER_URL_SIZE_REGEX, url):
        width, height = matches[0]

        return int(height) / int(width)


@app.post("/")
def movie_by_link(req: ResolverRequest):
    movie = get_byURL(req.imdbUrl)

    if not movie:
        match = re.search(".*tt(\d+)", req.imdbUrl)

        if match:
            imdb_id = match.group(1)
            movie = IMDb().get_movie(imdb_id)

    if not isinstance(movie, Movie):
        raise HTTPException(status_code=404, detail="Link couldn't be resolved to a movie")
    else:
        cover_url = movie.data["cover url"]
        cover_url = remove_size_from_cover_url(cover_url)
        cover_ratio = get_ratio_from_cover_url(cover_url)

        return {
            "id": movie.movieID,
            "title": movie.data['title'],
            "year": movie.data['year'],
            "rating": movie.data['rating'],
            "cover": {
                "url": cover_url,
                "ratio": cover_ratio,
            },
        }
