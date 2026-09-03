"""
avisar_lixo.py — Escala de Retirada de Lixo • Bispo Alimentos

- Segunda-feira: envia resumo semanal + aviso do dia
- Demais dias:   envia apenas aviso do dia

Uso manual:
  python avisar_lixo.py           -> execucao normal
  python avisar_lixo.py --teste   -> simula sem enviar nada
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
    "Out26": "PREENCHER",
    "Nov26": "PREENCHER",
    "Dez26": "PREENCHER",
}

SMTP_SERVIDOR = "smtp.gmail.com"
SMTP_PORTA = 587
SMTP_USUARIO = os.environ.get("SMTP_USUARIO")
SMTP_SENHA = os.environ.get("SMTP_SENHA")
NOME_REMETENTE = "Escala do Lixo - Bispo"

if not SMTP_USUARIO or not SMTP_SENHA:
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

MODO_TESTE = "--teste" in sys.argv

DIAS_PT = {
    "Monday": "segunda-feira", "Tuesday": "terca-feira",
    "Wednesday": "quarta-feira", "Thursday": "quinta-feira",
    "Friday": "sexta-feira", "Saturday": "sabado", "Sunday": "domingo",
}
_MESES = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

def aba_mes_atual():
    h = datetime.today()
    return f"{_MESES[h.month-1]}{str(h.year)[2:]}"

def gid_mes_atual():
    aba = aba_mes_atual()
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
        with urllib.request.urlopen(url, timeout=15) as r:
            return r.read().decode("utf-8")
    except Exception as e:
        print(f"Erro ao acessar planilha (gid={gid}): {e}")
        sys.exit(1)

def carregar_escala():
    ano = datetime.today().year
    escala = []
    for row in csv.reader(io.StringIO(baixar_csv(gid_mes_atual()))):
        if not row or not row[0].strip() or not row[0][0].isdigit(): continue
        d, nome = row[0].strip(), row[2].strip() if len(row)>2 else ""
        if not nome: continue
        try:
            data = datetime.strptime(f"{d}/{ano}" if d.count("/")==1 else d, "%d/%m/%Y").date()
        except ValueError: continue
        escala.append({"data": data, "nome": nome})
    return escala

def carregar_emails():
    emails = {}
    for i, row in enumerate(csv.reader(io.StringIO(baixar_csv(GID_EMAILS)))):
        if i==0 or len(row)<2 or not row[1].strip(): continue
        n, e = row[0].strip(), row[1].strip()
        if n and e: emails[normalizar(n)] = {"nome": n, "email": e}
    return emails

def enviar_email(nome, email, assunto, corpo):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"] = f"{NOME_REMETENTE} <{SMTP_USUARIO}>"
    msg["To"] = email
    msg.attach(MIMEText(corpo, "html", "utf-8"))
    try:
        with smtplib.SMTP(SMTP_SERVIDOR, SMTP_PORTA, timeout=15) as s:
            s.ehlo(); s.starttls(); s.login(SMTP_USUARIO, SMTP_SENHA)
            s.sendmail(SMTP_USUARIO, email, msg.as_string())
        print(f"  [OK] {nome} <{email}>")
    except smtplib.SMTPAuthenticationError:
        print("Falha SMTP: verifique usuario e senha de app do Gmail.")
        sys.exit(1)
    except Exception as e:
        print(f"  Erro ao enviar para {nome}: {e}")

def build_email(icone, titulo, conteudo):
    return f"""<html>
<body style="font-family:Arial,sans-serif;color:#333;max-width:520px;margin:auto;background:#e8edf2;padding:20px;">
<div style="border-radius:12px;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,0.18);">
<div style="background:white;padding:22px 32px;text-align:center;border-bottom:4px solid #C0392B;">
<img src="{LOGO_URL}" alt="Bispo Food Service" style="height:72px;display:block;margin:auto;">
</div>
<div style="background:linear-gradient(135deg,#1F4E79 0%,#2471A3 100%);color:white;padding:16px 24px;text-align:center;">
<h2 style="margin:0;font-size:17px;font-weight:bold;letter-spacing:0.4px;">{icone} {titulo}</h2>
</div>
<div style="background:white;padding:28px 32px;">
{conteudo}
</div>
<div style="background:#17406b;padding:14px 24px;text-align:center;">
<p style="font-size:11px;color:#8fb8d8;margin:0;line-height:1.9;">
Mensagem autom&#225;tica &bull; Escala de Retirada de Lixo &ndash; Bispo Alimentos<br>
Desenvolvido por Julio Meneghette | Analista de Tecnologia da Informa&#231;&#227;o
</p>
</div>
</div>
</body></html>"""

def corpo_diario(nome, data):
    dia = DIAS_PT.get(data.strftime("%A"), data.strftime("%A"))
    fmt = data.strftime("%d/%m/%Y")
    assunto = f"Lembrete: hoje e o seu dia de retirar o lixo! ({fmt})"
    conteudo = f"""
<p style="font-size:15px;">Ola, <strong>{nome}</strong>!</p>
<p>Este e um lembrete de que <strong>hoje, {dia} ({fmt})</strong>, e o seu dia de retirar o lixo.</p>
<div style="background:#EBF5FB;border-left:4px solid #2471A3;padding:12px 16px;border-radius:4px;margin:20px 0;font-size:14px;">
Nao esqueca de colocar o lixo no local correto <strong>antes da coleta</strong>!
</div>"""
    return assunto, build_email("&#128276;", "Lembrete: Retirada de Lixo", conteudo)

def corpo_semanal(nome, data):
    dia = DIAS_PT.get(data.strftime("%A"), data.strftime("%A"))
    fmt = data.strftime("%d/%m/%Y")
    assunto = f"Voce esta na escala do lixo essa semana! ({data.strftime('%d/%m')})"
    conteudo = f"""
<p style="font-size:15px;">Ola, <strong>{nome}</strong>!</p>
<p>Esta semana voce esta na escala de retirada de lixo.</p>
<div style="background:#FEF9E7;border-left:4px solid #F0A500;padding:14px 18px;border-radius:4px;margin:20px 0;">
<span style="font-size:13px;color:#888;">Seu dia de coleta:</span><br>
<strong style="font-size:16px;">{dia}, {fmt}</strong>
</div>
<p style="color:#666;font-size:13px;">Voce recebera um novo lembrete na manha do dia.</p>"""
    return assunto, build_email("&#128276;", "Escala da Semana &ndash; Retirada de Lixo", conteudo)

def main():
    hoje = datetime.today().date()
    is_seg = hoje.weekday() == 0

    print(f"{'='*50}")
    print(f"Data: {hoje.strftime('%d/%m/%Y')} | Aba: {aba_mes_atual()}")
    print(f"{'='*50}")

    if not MODO_TESTE and ja_enviado_hoje():
        print(f"\nJa houve um envio real hoje ({hoje.strftime('%d/%m/%Y')}). Nenhum novo e-mail sera enviado.")
        print(f"{'='*50}")
        return

    escala = carregar_escala()
    emails = carregar_emails()
    print(f"Registros: {len(escala)} | E-mails: {len(emails)}")

    if is_seg:
        seg = hoje
        sab = seg + timedelta(days=5)
        semana = [x for x in escala if seg <= x["data"] <= sab]
        print(f"\n[SEMANAL] {seg.strftime('%d/%m')} a {sab.strftime('%d/%m')} — {len(semana)} responsavel(is):")
        for r in semana:
            entrada = emails.get(normalizar(r["nome"]))
            if not entrada:
                print(f"  AVISO: {r['nome']} sem e-mail"); continue
            assunto, corpo = corpo_semanal(r["nome"], r["data"])
            if MODO_TESTE:
                print(f"  [TESTE] {r['nome']} — {r['data'].strftime('%d/%m/%Y')} -> {entrada['email']}")
            else:
                enviar_email(r["nome"], entrada["email"], assunto, corpo)

    print(f"\n[DIARIO] Responsavel de hoje:")
    resp = next((x for x in escala if x["data"] == hoje), None)
    if not resp:
        print("  Nenhum responsavel hoje.")
    else:
        entrada = emails.get(normalizar(resp["nome"]))
        if not entrada:
            print(f"  AVISO: {resp['nome']} sem e-mail.")
        else:
            assunto, corpo = corpo_diario(resp["nome"], hoje)
            if MODO_TESTE:
                print(f"  [TESTE] {resp['nome']} -> {entrada['email']}")
            else:
                enviar_email(resp["nome"], entrada["email"], assunto, corpo)

    if not MODO_TESTE:
        marcar_enviado_hoje()
        print(f"\nEnvio de hoje registrado em '{ARQUIVO_CONTROLE}'.")
    else:
        print(f"\nTeste concluido. Nenhum e-mail enviado.")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
