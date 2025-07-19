# api.py
import requests, uuid
from auth import get_token, APP_KEY, CERTS

BASE = "https://api-pix.bb.com.br/pix/v2"

def criar_cobranca(valor: float, chave_pix: str) -> dict:
    txid = uuid.uuid4().hex
    body = {
        "calendario": {"expiracao": 3600},
        "valor": {"original": f"{valor:.2f}"},
        "chave": chave_pix,
        "solicitacaoPagador": "Totem"
    }
    url = f"{BASE}/cob/{txid}"
    params = {"gw-app-key": APP_KEY}
    r = requests.put(url, params=params, json=body,
                     headers={"Authorization": f"Bearer {get_token()}"},
                     cert=CERTS, timeout=30)
    r.raise_for_status()
    resp = r.json()
    resp["txid"] = txid
    return resp

def status_cobranca(txid: str) -> str:
    url = f"{BASE}/cob/{txid}"
    params = {"gw-app-key": APP_KEY}
    r = requests.get(url, params=params,
                     headers={"Authorization": f"Bearer {get_token()}"},
                     cert=CERTS, timeout=30)
    r.raise_for_status()
    return r.json().get("status", "")
