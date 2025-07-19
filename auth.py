# auth.py
import time, base64, requests

CLIENT_ID     = "eyJpZCI6IjA1ZmZlYTEtYWRkMy00ZTVmLSIsImNvZGlnb1B1YmxpY2Fkb3IiOjAsImNvZGlnb1NvZnR3YXJlIjoxMTI2MjQsInNlcXVlbmNpYWxJbnN0YWxhY2FvIjoyfQ"
CLIENT_SECRET = "eyJpZCI6IjU0MTgwZjgtMmQ4Yi00NTdkLTgxMmQtODRhMWUiLCJjb2RpZ29QdWJsaWNhZG9yIjowLCJjb2RpZ29Tb2Z0d2FyZSI6MTEyNjI0LCJzZXF1ZW5jaWFsSW5zdGFsYWNhbyI6Miwic2VxdWVuY2lhbENyZWRlbmNpYWwiOjcsImFtYmllbnRlIjoicHJvZHVjYW8iLCJpYXQiOjE3NDgwOTgwNjUzMjd9"
APP_KEY       = "230ff50134f449f701ecca0d530061cd"
CERTS         = (r"C:\totem_pix\certificado.pem",
                 r"C:\totem_pix\chave_sem_senha.key")

_scope   = "cob.read cob.write pix.read pix.write"
_token   = None
_expires = 0

def _fetch_token():
    global _token, _expires
    basic = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {basic}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    params = {
        "grant_type": "client_credentials",
        "scope": _scope,
        "gw-app-key": APP_KEY,
    }
    r = requests.post("https://oauth.bb.com.br/oauth/token",
                      headers=headers, params=params,
                      cert=CERTS, timeout=30)
    r.raise_for_status()
    data = r.json()
    _token   = data["access_token"]
    _expires = time.time() + int(data["expires_in"]) - 30
    return _token

def get_token():
    global _token, _expires
    if _token is None or time.time() >= _expires:
        _fetch_token()
    return _token
