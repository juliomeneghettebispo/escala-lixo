"""
avisar_lixo.py — Escala de Retirada de Lixo • Bispo Alimentos

- Segunda-feira: envia resumo semanal + aviso do dia
- Demais dias:   envia apenas aviso do dia

Uso manual:
  python avisar_lixo.py           -> execucao normal
  python avisar_lixo.py --teste   -> simula sem enviar nada
  python avisar_lixo.py --completar-semana -> envia apenas avisos da semana no proximo mes
"""

import smtplib, sys, os, csv, io, urllib.request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from unicodedata import normalize

sys.stdout.reconfigure(encoding="utf-8")

LOGO_URL = "https://raw.githubusercontent.com/juliomeneghettebispo/escala-lixo/main/src/logo.png"

# ─── CONFIG ─────────────────────────────────────────────
SHEET_ID = "1txqXRtwt0FyH9gpHqSNLex2raO7Z6zjp4QZnRfr5f4o"
GID_EMAILS = "618358573"

GIDS_MESES = {
    "Mai26": "PREENCHER",
    "Jun26": "PREENCHER",
    "Jul26": "PREENCHER",
    "Ago26": "1416374903",
    "Set26": "708121321",
    "Out26": "309815557",
    "Nov26": "PREENCHER",
    "Dez26": "PREENCHER",
}

SMTP_SERVIDOR = "smtp.gmail.com"
SMTP_PORTA = 587
SMTP_USUARIO = os.environ.get("SMTP_USUARIO")
SMTP_SENHA = os.environ.get("SMTP_SENHA")
NOME_REMETENTE = "Escala do Lixo - Bispo"

MODO_TESTE = "--teste" in sys.argv
MODO_COMPLETAR = "--completar-semana" in sys.argv

if not MODO_TESTE and (not SMTP_USUARIO or not SMTP_SENHA):
    print("ERRO: variaveis de ambiente SMTP_USUARIO e/ou SMTP_SENHA nao definidas.")
    print("No GitHub Actions, configure-as em Settings > Secrets and variables > Actions")
    print("e garanta que o step 'Executar script' as repasse via 'env:'.")
    sys.exit(1)

# Arquivo de controle: guarda a data (AAAA-MM-DD) do ultimo envio real
# concluido. Ele fica versionado no repositorio para sobreviver entre
# execucoes do workflow, evitando envios duplicados no mesmo dia
# (ex.: execucao manual + execucao agendada no mesmo dia).
ARQUIVO_CONTROLE = "ultimo_envio.txt"
# ──────────────────────────────────────────────────────────

DIAS_PT = {
    "Monday": "segunda-feira", "Tuesday": "terca-feira",
    "Wednesday": "quarta-feira", "Thursday": "quinta-feira",
    "Friday": "sexta-feira", "Saturday": "sabado", "Sunday": "domingo",
}
_MESES = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

def aba_mes(data):
    return f"{_MESES[data.month-1]}{str(data.year)[2:]}"

def gid_mes(data):
    aba = aba_mes(data)
    gid = GIDS_MESES.get(aba)
    if not gid or gid == "PREENCHER":
        print(f"AVISO: GID da aba '{aba}' nao preenchido.")
        sys.exit(1)
    return gid

def normalizar(t):
    return normalize("NFD", t).encode("ascii","ignore").decode().lower().strip()

def ja_enviado_hoje():
    """Retorna True se ja existe um envio real registrado para a data de hoje."""
    try:
        with open(ARQUIVO_CONTROLE, "r", encoding="utf-8") as f:
            return f.read().strip() == datetime.today().date().isoformat()
    except FileNotFoundError:
        return False

def marcar_enviado_hoje():
    """Registra a data de hoje como ja processada (somente em envio real)."""
    with open(ARQUIVO_CONTROLE, "w", encoding="utf-8") as f:
        f.write(datetime.today().date().isoformat())

def baixar_csv(gid):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
    try:
