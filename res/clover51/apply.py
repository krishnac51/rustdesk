"""Clover51 branding for RustDesk builds.

Run in CI right after checkout:
    python3 res/clover51/apply.py --variant support|desk --platform windows|android

Builds the Clover51 server address, public key and API server into the client
(the documented way to make a custom RustDesk client), and sets the app name.
Reads the server public key from the CLOVER51_SERVER_KEY environment variable.
"""
import argparse
import io
import os
import re
import sys

SERVER = "medycheck.com"
API_SERVER = "https://medycheck.com/rust"
NAMES = {"support": "Clover51 Support", "desk": "Clover51 Desk"}
CONN_TYPE = {"support": "incoming", "desk": "outgoing"}


def patch(path, old, new):
    raw = io.open(path, encoding="utf-8", newline="").read()
    crlf = "\r\n" in raw
    if crlf:
        old, new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
    n = raw.count(old)
    if n != 1:
        sys.exit(f"{path}: expected 1 match, found {n}: {old[:70]!r}")
    io.open(path, "w", encoding="utf-8", newline="").write(raw.replace(old, new))
    print(f"patched {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=NAMES, required=True)
    ap.add_argument("--platform", choices=["windows", "android"], required=True)
    args = ap.parse_args()

    key = os.environ.get("CLOVER51_SERVER_KEY", "").strip()
    if not re.fullmatch(r"[A-Za-z0-9+/]{43}=", key):
        sys.exit("CLOVER51_SERVER_KEY secret is missing or not a valid RustDesk public key")
    name = NAMES[args.variant]

    cfg = "libs/hbb_common/src/config.rs"
    patch(cfg, 'pub const RENDEZVOUS_SERVERS: &[&str] = &["rs-ny.rustdesk.com"];',
          f'pub const RENDEZVOUS_SERVERS: &[&str] = &["{SERVER}"];')
    patch(cfg, 'pub const RS_PUB_KEY: &str = "OeVuKk5nlHiXp+APNn0Y3pC1Iwpwn44JGqrQCsWqmBw=";',
          f'pub const RS_PUB_KEY: &str = "{key}";')
    patch(cfg, 'pub static ref APP_NAME: RwLock<String> = RwLock::new("RustDesk".to_owned());',
          f'pub static ref APP_NAME: RwLock<String> = RwLock::new("{name}".to_owned());')

    patch("src/common.rs", '    "https://admin.rustdesk.com".to_owned()\n',
          f'    "{API_SERVER}".to_owned()\n')

    if args.platform == "windows":
        # Customers can only be controlled; technicians can only connect out.
        patch("src/common.rs", "pub fn load_custom_client() {\n",
              "pub fn load_custom_client() {\n"
              "    // Clover51: fixed connection direction for this build.\n"
              "    config::HARD_SETTINGS\n"
              "        .write()\n"
              "        .unwrap()\n"
              f'        .insert("conn-type".to_owned(), "{CONN_TYPE[args.variant]}".to_owned());\n')
        rc = "flutter/windows/runner/Runner.rc"
        patch(rc, 'VALUE "CompanyName", "Purslane Tech Pte. Ltd."',
              'VALUE "CompanyName", "Clover51"')
        patch(rc, 'VALUE "FileDescription", "RustDesk Remote Desktop"',
              f'VALUE "FileDescription", "{name}"')
        patch(rc, 'VALUE "ProductName", "RustDesk"',
              f'VALUE "ProductName", "{name}"')

    print(f"Clover51 {args.variant} ({args.platform}) applied")


if __name__ == "__main__":
    main()
