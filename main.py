from fastapi import FastAPI, HTTPException
from imdb.Movie import Movie
from imdb.helpers import get_byURL
from pydantic import BaseModel

app = FastAPI()


class ResolverRequest(BaseModel):
    imdbUrl: str


@app.post("/")
def movie_by_link(req: ResolverRequest):
    movie = get_byURL(req.imdbUrl)
    if not isinstance(movie, Movie):
        raise HTTPException(status_code=404, detail="Link couldn't be resolved to a movie")
    else:
        return {
            "id": movie.movieID,
            "title": movie.data['title'],
            "year": movie.data['year'],
            "rating": movie.data['rating']
        }
