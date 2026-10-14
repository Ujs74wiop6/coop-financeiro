"""Ponto de entrada do back-end (API REST em Flask, porta 5000)."""
from flask import Flask, jsonify
from flask_cors import CORS

import auth
import contas_pagar
import plano_contas

app = Flask(__name__)

# O front-end roda em outra porta (8080), então o navegador exige CORS.
# Aqui liberamos as origens do front-end para chamar a API.
CORS(app, origins=["http://localhost:8080", "http://127.0.0.1:8080"])

app.register_blueprint(auth.bp)
app.register_blueprint(plano_contas.bp)
app.register_blueprint(contas_pagar.bp)


@app.get("/api/health")
def health():
    """Rota pública só para checar se a API está no ar."""
    return jsonify(status="ok")


if __name__ == "__main__":
    auth.criar_admin_se_nao_existir()
    app.run(host="0.0.0.0", port=5000)
