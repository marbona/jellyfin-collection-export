from __future__ import annotations

from dataclasses import dataclass

import requests


class JellyfinError(RuntimeError):
    """Raised when Jellyfin communication fails."""


@dataclass(slots=True)
class Collection:
    id: str
    name: str


@dataclass(slots=True)
class Movie:
    id: str
    name: str
    path: str


class JellyfinClient:
    """Small wrapper around the Jellyfin REST API."""

    def __init__(self, base_url: str, api_key: str, timeout: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-Emby-Token": api_key,
                "Accept": "application/json",
            }
        )
        self._user_id: str | None = None

    def _admin_user_id(self) -> str:
        """A user id to satisfy endpoints that need one even for API-key requests.

        An API key alone has no associated user, and Jellyfin's single-item
        `/Items/{id}` endpoint errors out without a `userId` even though the
        `/Items` list endpoint works fine without one. Any user with library
        access works; prefer an administrator.
        """
        if self._user_id is None:
            users = self._get("/Users")
            admin = next((user for user in users if user.get("Policy", {}).get("IsAdministrator")), None)
            chosen = admin or (users[0] if users else None)
            if not chosen or not chosen.get("Id"):
                raise JellyfinError(
                    "No Jellyfin user found.\n"
                    "Create at least one user account and try again."
                )
            self._user_id = str(chosen["Id"])
        return self._user_id

    def _get(self, endpoint: str, params: dict[str, str] | None = None) -> dict | list:
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
        except requests.RequestException as exc:
            raise JellyfinError(
                "Cannot reach Jellyfin.\n"
                f"URL: {self.base_url}\n"
                "Check the server URL and network connectivity."
            ) from exc

        if response.status_code in {401, 403}:
            raise JellyfinError(
                "Jellyfin rejected the API key.\n"
                "The provided key is invalid or does not have enough permissions.\n"
                "Create a valid administrator API key and try again."
            )
        if not response.ok:
            detail = response.text.strip()
            raise JellyfinError(
                "Jellyfin returned an unexpected response.\n"
                f"HTTP status: {response.status_code}\n"
                f"Request: GET {url} params={params}\n"
                f"Response body: {detail or '<empty>'}"
            )
        return response.json()

    def validate_api_key(self) -> None:
        self._get("/Users")

    def list_collections(self) -> list[Collection]:
        payload = self._get(
            "/Items",
            params={
                "Recursive": "true",
                "IncludeItemTypes": "BoxSet",
                "Fields": "BasicSyncInfo",
            },
        )
        items = payload.get("Items", [])
        return [
            Collection(id=str(item["Id"]), name=str(item["Name"]))
            for item in items
            if item.get("Id") and item.get("Name")
        ]

    def get_collection(self, collection_id: str) -> Collection:
        payload = self._get(f"/Items/{collection_id}", params={"userId": self._admin_user_id()})
        if not payload.get("Id"):
            raise JellyfinError(
                "Collection not found in Jellyfin.\n"
                f"Collection id: {collection_id}\n"
                "Open `jce install` again and select an existing collection."
            )
        return Collection(id=str(payload["Id"]), name=str(payload["Name"]))

    def get_collection_movies(self, collection_id: str) -> list[Movie]:
        payload = self._get(
            "/Items",
            params={
                "ParentId": collection_id,
                "Recursive": "true",
                "IncludeItemTypes": "Movie",
                "Fields": "Path",
            },
        )
        movies: list[Movie] = []
        for item in payload.get("Items", []):
            path = item.get("Path")
            if not path:
                continue
            movies.append(
                Movie(
                    id=str(item["Id"]),
                    name=str(item["Name"]),
                    path=str(path),
                )
            )
        return movies
