"""Build the medycheck.com RustDesk server settings into a stock RustDesk client.

Run in CI right after checkout:
    python3 res/preconfig/apply.py

Sets the default ID/relay server, server public key and API server, so a
freshly installed client connects to our server with no manual setup.
Name, icons and everything else stay stock RustDesk.
Reads the server public key from the CLOVER51_SERVER_KEY environment variable.
"""
import io
import os
import re
import sys

SERVER = "medycheck.com"
API_SERVER = "https://medycheck.com/rust"


def patch(path, old, new):
    raw = io.open(path, encoding="utf-8", newline="").read()
    if "\r\n" in raw:
        old, new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
    n = raw.count(old)
    if n != 1:
        sys.exit(f"{path}: expected 1 match, found {n}: {old[:70]!r}")
    io.open(path, "w", encoding="utf-8", newline="").write(raw.replace(old, new))
    print(f"patched {path}")


def main():
    key = os.environ.get("CLOVER51_SERVER_KEY", "").strip()
    if not re.fullmatch(r"[A-Za-z0-9+/]{43}=", key):
        sys.exit("CLOVER51_SERVER_KEY secret is missing or not a valid RustDesk public key")

    cfg = "libs/hbb_common/src/config.rs"
    patch(cfg, 'pub const RENDEZVOUS_SERVERS: &[&str] = &["rs-ny.rustdesk.com"];',
          f'pub const RENDEZVOUS_SERVERS: &[&str] = &["{SERVER}"];')
    patch(cfg, 'pub const RS_PUB_KEY: &str = "OeVuKk5nlHiXp+APNn0Y3pC1Iwpwn44JGqrQCsWqmBw=";',
          f'pub const RS_PUB_KEY: &str = "{key}";')
    patch("src/common.rs", '    "https://admin.rustdesk.com".to_owned()\n',
          f'    "{API_SERVER}".to_owned()\n')
    # No "Download new version" banner: it links to the official build,
    # which has none of these settings. Updates come from our own server.
    patch("src/common.rs", "pub fn check_software_update() {\n    if is_custom_client() {\n",
          "pub fn check_software_update() {\n    if true {\n")
    print("medycheck server settings applied")


if __name__ == "__main__":
    main()
