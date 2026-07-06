"""Streamlit front end for the STRIDE Threat Modeling API."""
import base64
import io
import os
from pathlib import Path

import requests
import streamlit as st

API_URL = os.environ.get("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Modelagem de Ameaças STRIDE", page_icon="🛡️", layout="wide")
st.title("🛡️ Modelagem de Ameaças STRIDE por IA")
st.caption("Envie um diagrama de arquitetura e receba um relatório de ameaças STRIDE.")

with st.sidebar:
    st.header("Configurações")
    conf = st.slider("Confiança mínima da detecção", 0.1, 0.9, 0.4, 0.05)
    st.markdown("---")
    st.markdown(
        "**Como usar:** envie uma imagem PNG/JPG de um diagrama de arquitetura "
        "(ex.: diagramas de referência AWS/Azure)."
    )

uploaded = st.file_uploader("Diagrama de arquitetura", type=["png", "jpg", "jpeg", "webp"])

# ready-to-try examples: the two evaluation figures from the challenge PDF
_FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
_EXAMPLES = {
    "Arquitetura 1 (AWS)": _FIXTURES / "eval_arch1.png",
    "Arquitetura 2 (Azure)": _FIXTURES / "eval_arch2.png",
}
with st.sidebar:
    st.markdown("**Exemplos do desafio:**")
    example_choice = st.radio(
        "Usar figura de avaliação", ["(nenhum)", *[k for k, p in _EXAMPLES.items() if p.exists()]],
        label_visibility="collapsed",
    )

if uploaded is None and example_choice != "(nenhum)":
    path = _EXAMPLES[example_choice]
    uploaded = io.BytesIO(path.read_bytes())
    uploaded.name, uploaded.type = path.name, "image/png"
    uploaded.getvalue = lambda: path.read_bytes()

if uploaded is not None:
    with st.spinner("Analisando o diagrama..."):
        try:
            resp = requests.post(
                f"{API_URL}/analyze",
                files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type)},
                data={"conf_threshold": conf},
                timeout=120,
            )
        except requests.RequestException as exc:
            st.error(f"Não foi possível conectar à API em {API_URL}: {exc}")
            st.stop()

    if resp.status_code == 422:
        st.error("O arquivo enviado não é uma imagem válida.")
        st.stop()
    if resp.status_code != 200:
        st.error(f"Erro da API ({resp.status_code}): {resp.text}")
        st.stop()

    body = resp.json()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Diagrama original")
        st.image(uploaded)
    with col2:
        st.subheader("Componentes detectados")
        st.image(base64.b64decode(body["annotated_image_base64"]))

    if body["detections"]:
        st.subheader(f"Detecções ({len(body['detections'])})")
        st.dataframe(
            [
                {
                    "Componente": d["component_type"],
                    "Confiança": f"{d['confidence']:.2f}",
                    "Caixa (x1,y1,x2,y2)": str(tuple(int(v) for v in d["bbox"])),
                }
                for d in body["detections"]
            ],
            use_container_width=True,
        )
    else:
        st.warning("Nenhum componente detectado com o limite de confiança atual.")

    st.subheader("Relatório STRIDE")
    origem = "LLM (Claude)" if body["report_source"] == "llm" else "modelo determinístico"
    st.caption(f"Relatório gerado por: {origem}")
    st.markdown(body["report_markdown"])
    st.download_button(
        "⬇️ Baixar relatório (.md)",
        data=body["report_markdown"],
        file_name="relatorio-stride.md",
        mime="text/markdown",
    )
