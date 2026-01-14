import os
import pandas as pd
from flask import Flask, render_template, request, send_file, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "automacao-cnpj"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -------------------------------
# FUNÇÃO PRINCIPAL DA AUTOMAÇÃO
# -------------------------------
def rodar_automacao(cnpj_base, cnpj_improd, cpf_improd):
    # ---------- ETAPA 1 ----------
    p1 = pd.read_csv(cnpj_base)
    p2 = pd.read_csv(cnpj_improd)

    p1["Nome"] = p1["Nome"].astype(str).str.strip()
    p2["Nome"] = p2["Nome"].astype(str).str.strip()

    nomes_unicos = set(p1["Nome"]).symmetric_difference(set(p2["Nome"]))

    saida_p1 = p1[p1["Nome"].isin(nomes_unicos)]
    saida_p2 = p2[p2["Nome"].isin(nomes_unicos)]

    cnpj_produtivos = pd.concat([saida_p1, saida_p2], ignore_index=True)

    path_cnpj_prod = os.path.join(OUTPUT_DIR, "CNPJ_PRODUTIVOS.csv")
    cnpj_produtivos.to_csv(path_cnpj_prod, index=False)

    # ---------- ETAPA 2 ----------
    p3 = pd.read_csv(cpf_improd)
    p4 = pd.read_csv(path_cnpj_prod)

    p3.columns = p3.columns.str.strip()
    p4.columns = p4.columns.str.strip()

    p3["Nome fantasia"] = p3["Nome fantasia"].astype(str).str.strip()
    p4["Nome fantasia"] = p4["Nome fantasia"].astype(str).str.strip()

    nomes_comuns = set(p3["Nome fantasia"]) & set(p4["Nome fantasia"])

    resultado_final = p3[p3["Nome fantasia"].isin(nomes_comuns)]
    
        # Corrigir nome da coluna (sem alterar dados)
    if "PRESTADOR SEM SERVIÇO" in resultado_final.columns:
        resultado_final = resultado_final.rename(columns={
            "PRESTADOR SEM SERVIÇO": "INSTALADOR SEM SERVIÇO"
        })

    output_final = os.path.join(
        OUTPUT_DIR, "CPF_IMPRODUTIVOS_DE_CNPJ_PRODUTIVOS.csv"
    )
    resultado_final.to_csv(output_final, index=False)
    



    return output_final


# -------------------------------
# ROTAS
# -------------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            cnpj_base = request.files["cnpj_base"]
            cnpj_improd = request.files["cnpj_improd"]
            cpf_improd = request.files["cpf_improd"]

            path1 = os.path.join(UPLOAD_DIR, cnpj_base.filename)
            path2 = os.path.join(UPLOAD_DIR, cnpj_improd.filename)
            path3 = os.path.join(UPLOAD_DIR, cpf_improd.filename)

            cnpj_base.save(path1)
            cnpj_improd.save(path2)
            cpf_improd.save(path3)

            arquivo_final = rodar_automacao(path1, path2, path3)

            return send_file(
                arquivo_final,
                as_attachment=True,
                download_name="CPF_IMPRODUTIVOS_DE_CNPJ_PRODUTIVOS.csv"
            )

        except Exception as e:
            flash(f"Erro ao processar: {str(e)}")
            return redirect(url_for("index"))

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
