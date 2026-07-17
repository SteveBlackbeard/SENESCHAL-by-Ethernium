"""Ed25519-signed capability grants.

An unsigned grant is a JSON file any process can edit — an agent could forge its
own permissions. A signed grant turns least-privilege into a cryptographic
guarantee: the broker refuses any grant that was not signed by the operator's
key, that was modified after signing (capability escalation), or that has
expired. `sig_alg` is carried for crypto-agility (a post-quantum signer can drop
in without a format break).

`cryptography` is an optional extra (`pip install robinhood[security]`); every
import here is lazy so the rest of the tool keeps its zero-dependency core.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_KEY_DIR = ".robinhood/keys"
SIG_ALG = "ed25519"


def generate_keys(key_dir: str | Path = DEFAULT_KEY_DIR) -> tuple[Path, Path]:
    """Generate the operator's grant-signing keypair."""
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives import serialization

    key_dir = Path(key_dir)
    key_dir.mkdir(parents=True, exist_ok=True)
    private = ed25519.Ed25519PrivateKey.generate()
    priv_path = key_dir / "grant.priv"
    pub_path = key_dir / "grant.pub"
    priv_path.write_bytes(private.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    ))
    pub_path.write_bytes(private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    ))
    return priv_path, pub_path


def load_keys(key_dir: str | Path = DEFAULT_KEY_DIR) -> tuple[bytes | None, bytes | None]:
    key_dir = Path(key_dir)
    priv = key_dir / "grant.priv"
    pub = key_dir / "grant.pub"
    return (
        priv.read_bytes() if priv.exists() else None,
        pub.read_bytes() if pub.exists() else None,
    )


def _payload(grant: dict[str, Any]) -> bytes:
    clean = {k: v for k, v in grant.items() if k != "signature"}
    return json.dumps(clean, sort_keys=True).encode("utf-8")


def sign_grant(grant: dict[str, Any], private_bytes: bytes, public_bytes: bytes) -> dict[str, Any]:
    """Sign a grant document. The public key and algorithm tag are bound INTO the
    signed payload so neither can be swapped afterwards."""
    from cryptography.hazmat.primitives.asymmetric import ed25519

    grant["issued_at"] = grant.get("issued_at") or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    grant["public_key"] = public_bytes.hex()
    grant["sig_alg"] = SIG_ALG
    grant["signature"] = ed25519.Ed25519PrivateKey.from_private_bytes(private_bytes).sign(
        _payload(grant)
    ).hex()
    return grant


def verify_grant(grant: dict[str, Any], trusted_public: bytes) -> tuple[bool, str]:
    """Verify a signed grant against the operator's trusted public key.

    Fail-closed on: missing signature, key mismatch (someone re-signed with
    their own key), payload tampering (capability escalation), or expiry."""
    from cryptography.hazmat.primitives.asymmetric import ed25519

    signature = grant.get("signature", "")
    if not signature:
        return False, "grant is unsigned"
    if grant.get("public_key", "") != trusted_public.hex():
        return False, "grant was signed by an untrusted key"
    try:
        ed25519.Ed25519PublicKey.from_public_bytes(trusted_public).verify(
            bytes.fromhex(signature), _payload(grant)
        )
    except Exception:
        return False, "signature does not match the grant (grant was modified after signing)"

    expires = grant.get("expires")
    if expires:
        try:
            deadline = datetime.fromisoformat(str(expires))
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
        except ValueError:
            return False, "grant has an invalid expiry timestamp"
        if datetime.now(timezone.utc) > deadline:
            return False, f"grant expired at {expires}"
    return True, "grant signature verified"


def signing_available() -> bool:
    try:
        import cryptography  # noqa: F401
        return True
    except ImportError:
        return False
