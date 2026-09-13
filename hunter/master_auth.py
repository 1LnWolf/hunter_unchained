import gnupg
import os
import secrets

def authenticate(config: dict) -> bool:
    method = config["master"]["auth_method"]
    if method == "gpg":
        return gpg_auth(config)
    elif method == "fido2":
        print("[!] FIDO2 not implemented yet.")
        return False
    else:
        print(f"Unknown auth method: {method}")
        return False

def gpg_auth(config) -> bool:
    gpg_home = os.environ.get("HUNTER_MASTER_GPG_KEYRING", os.path.expanduser("~/.gnupg"))
    gpg = gnupg.GPG(gnupghome=gpg_home)
    fingerprint = config["master"]["gpg_key_fingerprint"].replace(" ", "")
    challenge = secrets.token_hex(32)
    print("[AUTH] Sign the following challenge with your GPG key:")
    print(f"      {challenge}")
    print("(e.g., echo -n '<challenge>' | gpg --clearsign)")
    signed = input("Paste signed challenge: ")
    verified = gpg.verify(signed)
    if verified.valid and verified.fingerprint.replace(" ", "") == fingerprint:
        if challenge in str(verified.data):
            return True
    return False