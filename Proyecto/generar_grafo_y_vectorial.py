from code_python.crear_grafo_networkx import crear_grafo_metricas_mensuales
from code_python.crear_corpus_vectorial import crear_corpus_vectorial_hgm_faiss


def main():
    print("Generando grafo NetworkX.")
    crear_grafo_metricas_mensuales()

    print("\nGenerando indice vectorial FAISS.")
    crear_corpus_vectorial_hgm_faiss()


if __name__ == "__main__":
    main()
