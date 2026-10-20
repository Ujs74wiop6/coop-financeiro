"""Ponto de entrada do back-end (API REST em Flask, porta 5000)."""
from dotenv import load_dotenv

load_dotenv()  # lê o arquivo .env (no Docker, as variáveis já vêm prontas)

from flask import Flask, jsonify  # noqa: E402

from apps.login.controller import login_controller  # noqa: E402
from routes import contas_pagar_routes, login_routes, plano_contas_routes  # noqa: E402

app = Flask(__name__)
app.json.ensure_ascii = False  # acentos legíveis no JSON

app.register_blueprint(login_routes.bp)
app.register_blueprint(plano_contas_routes.bp)
app.register_blueprint(contas_pagar_routes.bp)


@app.get("/api/health")
def health():
    """Rota pública só para checar se a API está no ar."""
    return jsonify(status="ok")


if __name__ == "__main__":
    login_controller.criar_admin_se_nao_existir()
    app.run(host="0.0.0.0", port=5000)
