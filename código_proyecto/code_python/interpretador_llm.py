from pathlib import Path
import json

import numpy as np
import pandas as pd
from llama_cpp import Llama


LLM_INTERPRETADOR = None


def _rutas_interpretador():
    carpeta_codigo = Path(__file__).resolve().parent
    carpeta_proyecto = carpeta_codigo.parent

    return {
        "carpeta_codigo": carpeta_codigo,
        "carpeta_proyecto": carpeta_proyecto,
        "modelo": carpeta_proyecto / "modelos" / "modelos" / "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "contexto": carpeta_codigo / "contexto_interpretador_llm.txt",
    }


def _obtener_llm_interpretador():
    """
    Intenta reutilizar el mismo modelo cargado por consultas_llm.py.
    Si no está disponible, carga el modelo localmente.
    """
    global LLM_INTERPRETADOR

    try:
        from consultas_llm import _obtener_llm
        return _obtener_llm()
    except Exception:
        pass

    rutas = _rutas_interpretador()

    if LLM_INTERPRETADOR is None:
        print("Cargando modelo LLaMA para interpretación...")
        LLM_INTERPRETADOR = Llama(
            model_path=str(rutas["modelo"]),
            n_ctx=8192,
            n_threads=8,
            n_batch=128,
            logits_all=False,
            verbose=False
        )

    return LLM_INTERPRETADOR


def _leer_contexto_interpretador():
    rutas = _rutas_interpretador()
    return rutas["contexto"].read_text(encoding="utf-8")


def _valor_seguro(valor):
    if isinstance(valor, (np.integer,)):
        return int(valor)
    if isinstance(valor, (np.floating,)):
        if np.isnan(valor):
            return None
        return float(valor)
    if isinstance(valor, (np.ndarray,)):
        return valor.tolist()
    if pd.isna(valor) if not isinstance(valor, (list, dict, tuple, set)) else False:
        return None
    return valor


def _limpiar_para_json(objeto, max_filas=15):
    if isinstance(objeto, pd.DataFrame):
        return {
            "tipo": "dataframe",
            "filas_totales": int(len(objeto)),
            "columnas": list(objeto.columns),
            "muestra": objeto.head(max_filas).where(pd.notna(objeto), None).to_dict(orient="records")
        }

    if isinstance(objeto, pd.Series):
        return objeto.head(max_filas).where(pd.notna(objeto), None).to_dict()

    if isinstance(objeto, dict):
        limpio = {}
        for clave, valor in objeto.items():
            if clave == "dataframe" and isinstance(valor, pd.DataFrame):
                limpio[clave] = _limpiar_para_json(valor, max_filas=max_filas)
            else:
                limpio[clave] = _limpiar_para_json(valor, max_filas=max_filas)
        return limpio

    if isinstance(objeto, list):
        return [_limpiar_para_json(x, max_filas=max_filas) for x in objeto[:max_filas]]

    if isinstance(objeto, tuple):
        return [_limpiar_para_json(x, max_filas=max_filas) for x in objeto[:max_filas]]

    return _valor_seguro(objeto)


def _compactar_resultado(pregunta, resultado, max_caracteres=9000):
    compacto = {
        "pregunta": pregunta,
        "backend": resultado.get("backend") if isinstance(resultado, dict) else None,
        "accion": resultado.get("accion") if isinstance(resultado, dict) else None,
        "plan": resultado.get("plan") if isinstance(resultado, dict) else None,
        "resultado": resultado.get("resultado") if isinstance(resultado, dict) else resultado,
    }

    compacto = _limpiar_para_json(compacto)

    texto = json.dumps(compacto, ensure_ascii=False, indent=2, default=str)

    if len(texto) > max_caracteres:
        texto = texto[:max_caracteres] + "\n[RESULTADO RECORTADO POR LONGITUD]"

    return texto


def interpretar_llm(pregunta, resultado, imprimir=True):
    contexto = _leer_contexto_interpretador()
    llm = _obtener_llm_interpretador()
    resultado_compacto = _compactar_resultado(pregunta, resultado)

    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
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
        max_tokens=450,
        temperature=0.1,
        top_p=0.9,
        repeat_penalty=1.1,
        stop=["<|eot_id|>"]
    )

    interpretacion = salida["choices"][0]["text"].strip()

    if imprimir:
        print("\n===== INTERPRETACIÓN DEL LLM =====")
        print(interpretacion)

    return {
        "pregunta": pregunta,
        "interpretacion": interpretacion,
        "resultado_base": resultado
    }
