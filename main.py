from fastapi import FastAPI, HTTPException
from imdb import IMDb
from imdb.Movie import Movie
from imdb.helpers import get_byURL
from pydantic import BaseModel

import re


app = FastAPI()


class ResolverRequest(BaseModel):
    imdbUrl: str


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
        return {
            "id": movie.movieID,
            "title": movie.data['title'],
            "year": movie.data['year'],
            "rating": movie.data['rating'],
            "coverUrl": movie.data["cover url"],
        }
