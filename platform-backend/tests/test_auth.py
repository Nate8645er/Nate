"""Keycloak-Verifier — getestet ohne laufenden Keycloak (selbst signiert)."""

import json
import time

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

from app.platform.auth import KeycloakVerifier, OidcConfig, Principal, TokenError

ISSUER = "https://auth.example.com/realms/kunden"
KID = "test-key-1"


def _keypair_and_jwks():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub_jwk = json.loads(RSAAlgorithm.to_jwk(key.public_key()))
    pub_jwk["kid"] = KID
    pub_jwk["alg"] = "RS256"
    pub_jwk["use"] = "sig"
    return key, {"keys": [pub_jwk]}


def _make_token(key, claims, kid=KID):
    return jwt.encode(claims, key, algorithm="RS256", headers={"kid": kid})


def _verifier(jwks, audience=None):
    return KeycloakVerifier(OidcConfig(issuer=ISSUER, audience=audience), lambda: jwks)


def test_gueltiges_token_ergibt_principal():
    key, jwks = _keypair_and_jwks()
    now = int(time.time())
    token = _make_token(key, {
        "sub": "user-123", "iss": ISSUER, "iat": now, "exp": now + 300,
        "email": "a@b.ch", "realm_access": {"roles": ["kunde", "admin"]},
    })
    p = _verifier(jwks).verify(token)
    assert isinstance(p, Principal)
    assert p.subject == "user-123"
    assert p.tenant == "kunden"          # Realm aus dem Issuer
    assert "admin" in p.roles
    assert p.email == "a@b.ch"


def test_abgelaufenes_token_wird_abgelehnt():
    key, jwks = _keypair_and_jwks()
    now = int(time.time())
    token = _make_token(key, {"sub": "x", "iss": ISSUER, "iat": now - 600, "exp": now - 300})
    try:
        _verifier(jwks).verify(token)
    except TokenError:
        pass
    else:
        raise AssertionError("abgelaufenes Token haette abgelehnt werden muessen")


def test_falscher_aussteller_wird_abgelehnt():
    key, jwks = _keypair_and_jwks()
    now = int(time.time())
    token = _make_token(key, {"sub": "x", "iss": "https://boese/realms/x", "iat": now, "exp": now + 300})
    try:
        _verifier(jwks).verify(token)
    except TokenError:
        pass
    else:
        raise AssertionError("falscher Issuer haette abgelehnt werden muessen")


def test_unbekannte_kid_wird_abgelehnt():
    key, jwks = _keypair_and_jwks()
    now = int(time.time())
    token = _make_token(key, {"sub": "x", "iss": ISSUER, "iat": now, "exp": now + 300}, kid="fremd")
    try:
        _verifier(jwks).verify(token)
    except TokenError:
        pass
    else:
        raise AssertionError("unbekannte kid haette abgelehnt werden muessen")


def test_expliziter_tenant_claim_hat_vorrang():
    key, jwks = _keypair_and_jwks()
    now = int(time.time())
    token = _make_token(key, {
        "sub": "x", "iss": ISSUER, "iat": now, "exp": now + 300, "tenant": "acme-gmbh",
    })
    assert _verifier(jwks).verify(token).tenant == "acme-gmbh"
