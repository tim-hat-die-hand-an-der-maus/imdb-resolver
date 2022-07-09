from typing import Dict

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

IGNORE_FIELDS = {"cover", "coverUrl", "rating"}


def get_test_data():
    return {
        "https://imdb.com/title/tt9866072": {
            "code": 200,
            "data": {
                "id": "9866072",
                "title": "Holidate",
                "year": 2020,
            }
        }
    }


def compare_reults_by_url(imdb_id: str, actual: Dict):
    expected: Dict = get_test_data()[imdb_id]["data"]
    comparable_keys = expected.keys() - IGNORE_FIELDS

    result = {}
    for key in comparable_keys:
        result[key] = expected[key] == actual[key]

    return result


def test_url():
    for url in get_test_data().keys():
        response = client.post(
            "/",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            json={"imdbUrl": url}
        )

        assert response.status_code == get_test_data()[url].get("code", 200)
        assert all(e[1] for e in compare_reults_by_url(url, response.json()).items())
