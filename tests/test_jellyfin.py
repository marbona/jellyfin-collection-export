from unittest.mock import Mock, patch

import pytest

from jce.jellyfin import JellyfinClient, JellyfinError


def _response(status_code: int = 200, payload: dict | list | None = None) -> Mock:
    response = Mock()
    response.status_code = status_code
    response.ok = 200 <= status_code < 300
    response.text = ""
    response.json.return_value = payload if payload is not None else {}
    return response


def test_validate_api_key_rejects_unauthorized() -> None:
    client = JellyfinClient("http://localhost:8096", "bad-key")
    with patch.object(client.session, "get", return_value=_response(401)):
        with pytest.raises(JellyfinError, match="rejected the API key"):
            client.validate_api_key()


def test_list_collections_filters_incomplete_items() -> None:
    client = JellyfinClient("http://localhost:8096", "good-key")
    payload = {
        "Items": [
            {"Id": "1", "Name": "Guest Movies"},
            {"Name": "Missing id"},
        ]
    }
    with patch.object(client.session, "get", return_value=_response(200, payload)):
        collections = client.list_collections()

    assert len(collections) == 1
    assert collections[0].id == "1"
    assert collections[0].name == "Guest Movies"


def test_get_collection_movies_skips_items_without_path() -> None:
    client = JellyfinClient("http://localhost:8096", "good-key")
    payload = {
        "Items": [
            {"Id": "10", "Name": "Movie A", "Path": "/mnt/video/Movie A/Movie A.mkv"},
            {"Id": "11", "Name": "Movie B"},
        ]
    }
    with patch.object(client.session, "get", return_value=_response(200, payload)):
        movies = client.get_collection_movies("collection-id")

    assert len(movies) == 1
    assert movies[0].id == "10"
    assert movies[0].path == "/mnt/video/Movie A/Movie A.mkv"


def test_get_collection_uses_admin_user_id() -> None:
    client = JellyfinClient("http://localhost:8096", "good-key")
    users = [
        {"Id": "regular-user", "Policy": {"IsAdministrator": False}},
        {"Id": "admin-user", "Policy": {"IsAdministrator": True}},
    ]
    collection_payload = {"Id": "abc123", "Name": "Guest Movies"}

    with patch.object(
        client.session,
        "get",
        side_effect=[_response(200, users), _response(200, collection_payload)],
    ) as get_mock:
        collection = client.get_collection("abc123")

    assert collection.id == "abc123"
    assert collection.name == "Guest Movies"
    second_call_params = get_mock.call_args_list[1].kwargs["params"]
    assert second_call_params == {"userId": "admin-user"}


def test_get_collection_falls_back_to_first_user_without_admin() -> None:
    client = JellyfinClient("http://localhost:8096", "good-key")
    users = [{"Id": "only-user", "Policy": {"IsAdministrator": False}}]

    with patch.object(
        client.session,
        "get",
        side_effect=[_response(200, users), _response(200, {"Id": "abc123", "Name": "Guest Movies"})],
    ) as get_mock:
        client.get_collection("abc123")

    assert get_mock.call_args_list[1].kwargs["params"] == {"userId": "only-user"}


def test_get_collection_raises_when_no_users_exist() -> None:
    client = JellyfinClient("http://localhost:8096", "good-key")
    with patch.object(client.session, "get", return_value=_response(200, [])):
        with pytest.raises(JellyfinError, match="No Jellyfin user found"):
            client.get_collection("abc123")


def test_connection_error_raises_jellyfin_error() -> None:
    import requests

    client = JellyfinClient("http://localhost:8096", "good-key")
    with patch.object(client.session, "get", side_effect=requests.ConnectionError("boom")):
        with pytest.raises(JellyfinError, match="Cannot reach Jellyfin"):
            client.validate_api_key()
