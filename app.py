from flask import Flask, render_template, jsonify, request
from email.mime.text import MIMEText
from email.utils import formataddr
import smtplib
from dotenv import load_dotenv
import requests, random, datetime, os
from gtts import gTTS

load_dotenv()

# ===== Variaveis Globais =====
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

EMAIL_INTRO = """Olá, {nome_assinante},

É um prazer enorme conectar você ao *Salmos da Esperança* 🌿.

Em meio à correria e aos desafios que a vida nos apresenta, reservamos este momento especial para lhe entregar uma âncora de paz. 
Acreditamos que nas palavras dos Salmos encontramos a fonte inesgotável de força, conforto e luz para a nossa jornada.

Que este trecho da Escritura seja um farol para o seu dia, renovando sua fé e enchendo seu coração de coragem e esperança. 
Permita que esta palavra inspire a sua reflexão e guie seus passos.

A meditação de hoje é:
"""
EMAIL_TEMPLATE_HTML = """
<html>
  <body style="font-family: 'Segoe UI', Roboto, sans-serif; background-color: #f7f7f7; padding: 20px;">
    <div style="max-width: 650px; margin: auto; background-color: #ffffff; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); padding: 30px;">
      <p style="font-size: 1.1rem;">Olá, <strong>{nome_assinante}</strong>,</p>

      <p style="text-align: justify; line-height: 1.6;">
        É um prazer enorme conectar você ao <strong>Salmos da Esperança 🌿</strong>.
      </p>
      <p style="text-align: justify; line-height: 1.6;">
        Em meio à correria e aos desafios que a vida nos apresenta, reservamos este momento especial para lhe entregar uma âncora de paz. 
        Acreditamos que nas palavras dos Salmos encontramos a fonte inesgotável de força, conforto e luz para a nossa jornada.
      </p>
      <p style="text-align: justify; line-height: 1.6;">
        Que este trecho da Escritura seja um farol para o seu dia, renovando sua fé e enchendo seu coração de coragem e esperança. 
        Permita que esta palavra inspire a sua reflexão e guie seus passos.
      </p>

      <p style="margin-top: 30px; font-weight: bold; font-size: 1.1rem;">A meditação de hoje é:</p>

      <div style="margin: 25px 0; padding: 20px; border-left: 5px solid #0d6efd; background-color: #f1f6ff; border-radius: 8px;">
        <p style="white-space: pre-wrap; font-size: 1.05rem; line-height: 1.6;">{texto_salmo}</p>
      </div>

      <p style="margin-top: 30px; font-size: 0.95rem; color: #555;">
        Que a paz de Deus, que excede todo entendimento, guarde o seu coração e os seus pensamentos em Cristo Jesus.
      </p>

      <hr style="margin-top: 30px; border: none; border-top: 1px solid #ddd;">
      <p style="text-align: center; font-size: 0.9rem; color: #888; margin-top: 20px;">
        <em>Com carinho,<br>Equipe Salmos da Esperança 🌿</em>
      </p>
    </div>
  </body>
</html>
"""


app = Flask(__name__)

# ===== Funções utilitárias =====

def buscar_salmo(salmo_numero):
    url = f"https://bible-api.com/salmos+{salmo_numero}?translation=almeida"
    response = requests.get(url)
    return response.json()

def devocional_diario():
    dia = datetime.datetime.now().day
    salmo_numero = (dia % 150) or 150
    data = buscar_salmo(salmo_numero)
    texto = " ".join([v["text"].strip() for v in data["verses"]])
    return f"📖 Salmo {salmo_numero}\n\n{texto}"

def versiculo_aleatorio():
    salmo_numero = random.randint(1, 150)
    data = buscar_salmo(salmo_numero)
    total = len(data["verses"])
    versiculo_num = random.randint(1, total)
    versiculo = data["verses"][versiculo_num - 1]
    return f"📖 Salmo {salmo_numero}:{versiculo_num}\n“{versiculo['text'].strip()}”"

def gerar_audio(texto):
    os.makedirs("static/audio", exist_ok=True)
    caminho = os.path.join("static/audio", "devocional.mp3")
    tts = gTTS(texto, lang="pt-br")
    tts.save(caminho)
    return "/static/audio/devocional.mp3"

# ===== Rotas Flask =====

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/salmo-aleatorio")
def salmo_aleatorio():
    texto = versiculo_aleatorio()
    return render_template("devocional.html", titulo="Salmo Aleatório", texto=texto)

@app.route("/devocional")
def devocional():
    texto = devocional_diario()
    return render_template("devocional.html", titulo="Devocional Diário", texto=texto)

@app.route("/voz", methods=["POST"])
def voz():
    data = request.json
    texto = data.get("texto", "")

    if not texto:
        return jsonify({"error": "Texto não fornecido"}), 400

    caminho_audio = gerar_audio(texto)
    return jsonify({"audio_url": caminho_audio})

@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    
    return render_template("registro.html")

@app.route("/enviar-email", methods=["POST"])
def enviar_email():
    dados = request.get_json()
    destino = dados.get("email")
    texto = dados.get("texto")

    if not destino or not texto:
        return jsonify({"message": "E-mail não informado, ou dados incompletos."}), 400

    try:
        #remetente = EMAIL_USER
       # senha = EMAIL_PASS
        nome_assinante = destino.split("@")[0]
        corpo_email_html = EMAIL_TEMPLATE_HTML.format(
            nome_assinante=nome_assinante,
            texto_salmo=texto.replace("\n", "<br>")
        ) 
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "api-key": os.getenv("BREVO_API_KEY")
        }
        # msg = MIMEText(corpo_email_html, "html", "utf-8")
        # # msg = MIMEText(corpo_email, "plain", "utf-8")
        # msg["Subject"] = "Seu Devocional Diário 🌿"
        # msg["From"] = formataddr(("Salmos da Esperança 🌿", remetente))
        # msg["To"] = destino

        # with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        #     smtp.login(remetente, senha)
        #     smtp.send_message(msg)

        # return jsonify({"message": f"E-mail enviado com sucesso para {destino}!"})
        data = {
            "sender": {"name": "Salmos da Esperança 🌿", "email": "inovaglc@gmail.com"},
            "to": [{"email": destino}],
            "subject": "Seu Devocional Diário 🌿",
            "htmlContent": corpo_email_html
        }
        resp = requests.post(url, headers=headers, json=data, timeout=15)
        print("Brevo status:", resp.status_code, resp.text)
        if resp.status_code in (200, 201):
            return jsonify({"message": f"E-mail enviado com sucesso para {destino}!"})
        else:
            return jsonify({"message": "Erro ao enviar e-mail via Brevo.", "detail": resp.text}), 500
    except Exception as e:
        print(e)
        return jsonify({"message": "Erro ao enviar e-mail."}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
