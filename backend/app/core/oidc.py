import json
from functools import lru_cache
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.core.config import settings


def _provider_label() -> str:
    return settings.SECURITY_PROVIDER or "OIDC"


def _get_json(url: str) -> dict:
    with urlopen(url) as response:
        return json.loads(response.read().decode("utf-8"))


@lru_cache(maxsize=1)
def _get_discovery() -> dict:
    if not settings.oidc_issuer:
        return {}

    discovery_url = f"{settings.oidc_issuer}.well-known/openid-configuration"
    try:
        return _get_json(discovery_url)
    except (HTTPError, URLError):
        return {}


def _jwks_url() -> str:
    jwks_url = settings.OIDC_JWKS_URL or _get_discovery().get("jwks_uri") or settings.oidc_jwks_url
    if not jwks_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{_provider_label()} JWKS URL is not configured",
        )
    return jwks_url


def _userinfo_url() -> str | None:
    return settings.OIDC_USERINFO_URL or _get_discovery().get("userinfo_endpoint") or settings.oidc_userinfo_url


@lru_cache(maxsize=1)
def _get_jwks():
    return _get_json(_jwks_url())


def verify_oidc_id_token(token: str) -> dict:
    if not settings.oidc_issuer or not settings.oidc_client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{_provider_label()} is not configured",
        )

    try:
        header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token header: {exc}")

    algorithms = settings.oidc_algorithms
    if header.get("alg") not in algorithms:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unsupported token algorithm: {header.get('alg')}. Expected one of: {', '.join(algorithms)}.",
        )

    key = next((item for item in _get_jwks().get("keys", []) if item.get("kid") == header.get("kid")), None)
    if not key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Signing key not found for kid: {header.get('kid')}")

    try:
        return jwt.decode(
            token,
            key,
            algorithms=algorithms,
            audience=settings.oidc_audience,
            issuer=settings.oidc_issuer,
        )
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {exc}")


def get_oidc_userinfo(access_token: str) -> dict:
    userinfo_url = _userinfo_url()
    if not userinfo_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{_provider_label()} userinfo URL is not configured",
        )

    request = Request(userinfo_url, headers={"Authorization": f"Bearer {access_token}"})
    try:
        with urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Userinfo rejected token: {exc.code}")
    except URLError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Userinfo unavailable: {exc.reason}")


def get_oidc_profile(token: str) -> dict:
    try:
        return get_oidc_userinfo(token)
    except HTTPException as exc:
        if exc.status_code != status.HTTP_401_UNAUTHORIZED:
            raise

    return verify_oidc_id_token(token)
