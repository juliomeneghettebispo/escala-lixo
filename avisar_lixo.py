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

LOGO_B64 = "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"

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
<img src="data:image/png;base64,{LOGO_B64}" alt="Bispo Food Service" style="height:72px;display:block;margin:auto;">
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
