from pathlib import Path
import json

import numpy as np
import pandas as pd
from llama_cpp import Llama

from code_python.config import RUTA_MODELO


LLM_INTERPRETADOR_N_CTX = 8192
LLM_INTERPRETADOR_N_THREADS = 8
LLM_INTERPRETADOR_N_BATCH = 128
INTERPRETADOR_MAX_TOKENS = 350
INTERPRETADOR_TEMPERATURE = 0.1
INTERPRETADOR_TOP_P = 0.9
INTERPRETADOR_REPEAT_PENALTY = 1.1
MAX_CARACTERES_RESULTADO = 7000

LLM_INTERPRETADOR = None


def _rutas_interpretador():
    carpeta_codigo = Path(__file__).resolve().parent
    return {
        "modelo": RUTA_MODELO,
        "contexto": carpeta_codigo / "contexto_interpretador_llm.txt",
    }


def _obtener_llm_interpretador():
    global LLM_INTERPRETADOR

    try:
        from code_python.consultas_llm import _obtener_llm
        return _obtener_llm()
    except Exception:
        pass

    rutas = _rutas_interpretador()

    if LLM_INTERPRETADOR is None:
        print("Cargando modelo LLaMA para interpretacion...")
        LLM_INTERPRETADOR = Llama(
            model_path=str(rutas["modelo"]),
            n_ctx=LLM_INTERPRETADOR_N_CTX,
            n_threads=LLM_INTERPRETADOR_N_THREADS,
            n_batch=LLM_INTERPRETADOR_N_BATCH,
            logits_all=False,
            verbose=False
        )

    return LLM_INTERPRETADOR


def _leer_contexto_interpretador():
    rutas = _rutas_interpretador()
    return rutas["contexto"].read_text(encoding="utf-8")


def _valor_seguro(valor):
    if isinstance(valor, np.integer):
        return int(valor)
    if isinstance(valor, np.floating):
        if np.isnan(valor):
            return None
        return float(valor)
    if isinstance(valor, np.ndarray):
        return valor.tolist()
    if pd.isna(valor) if not isinstance(valor, (list, dict, tuple, set)) else False:
        return None
    return valor


def _limpiar_para_json(objeto, max_filas=15):
    if isinstance(objeto, pd.DataFrame):
        muestra = objeto.head(max_filas).where(pd.notna(objeto), None).to_dict(orient="records")
        return {
            "tipo": "dataframe",
            "filas_totales": int(len(objeto)),
            "columnas": list(objeto.columns),
            "muestra": muestra
        }

    if isinstance(objeto, pd.Series):
        return objeto.head(max_filas).where(pd.notna(objeto), None).to_dict()

    if isinstance(objeto, dict):
        return {clave: _limpiar_para_json(valor, max_filas=max_filas) for clave, valor in objeto.items()}

    if isinstance(objeto, list):
        return [_limpiar_para_json(valor, max_filas=max_filas) for valor in objeto[:max_filas]]

    if isinstance(objeto, tuple):
        return [_limpiar_para_json(valor, max_filas=max_filas) for valor in objeto[:max_filas]]

    return _valor_seguro(objeto)


def _compactar_resultado(pregunta, resultado, max_caracteres=MAX_CARACTERES_RESULTADO):
    compacto = {
        "pregunta": pregunta,
        "backend": resultado.get("backend") if isinstance(resultado, dict) else None,
        "accion": resultado.get("accion") if isinstance(resultado, dict) else None,
        "plan": resultado.get("plan") if isinstance(resultado, dict) else None,
        "resultado": resultado.get("resultado") if isinstance(resultado, dict) else resultado,
    }

    texto = json.dumps(_limpiar_para_json(compacto), ensure_ascii=False, indent=2, default=str)

    if len(texto) > max_caracteres:
        texto = texto[:max_caracteres] + "\n[RESULTADO RECORTADO POR LONGITUD]"

    return texto


def interpretar_llm(pregunta, resultado, imprimir=True):
    contexto = _leer_contexto_interpretador()
    llm = _obtener_llm_interpretador()
    resultado_compacto = _compactar_resultado(pregunta, resultado)

    prompt = f"""<|start_header_id|>system<|end_header_id|>
{contexto}
<|eot_id|><|start_header_id|>user<|end_header_id|>
Pregunta original:
{pregunta}

Resultado ejecutado:
{resultado_compacto}

Interpreta el resultado de forma breve, descriptiva y limitada a los datos recibidos.
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""

    salida = llm.create_completion(
        prompt=prompt,
        max_tokens=INTERPRETADOR_MAX_TOKENS,
        temperature=INTERPRETADOR_TEMPERATURE,
        top_p=INTERPRETADOR_TOP_P,
        repeat_penalty=INTERPRETADOR_REPEAT_PENALTY,
        stop=["<|eot_id|>"]
    )

    interpretacion = salida["choices"][0]["text"].strip()

    if imprimir:
        print("\nInterpretacion del LLM:")
        print(interpretacion)

    return interpretacion
