import json
import os
from main import gerar_resposta_segura 

def carregar_casos_de_teste(caminho_json="test_cases.json"):
    if not os.path.exists(caminho_json):
        raise FileNotFoundError(f"Arquivo {caminho_json} não encontrado.")
    with open(caminho_json, "r", encoding="utf-8") as f:
        return json.load(f)

def executar_pipeline_de_testes():
    casos = carregar_casos_de_teste()
    total_testes = len(casos)
    sucessos = 0
    falhas = 0
    
    print("==================================================")
    print(f" INICIANDO VALIDAÇÃO DE GUARDRAILS ({total_testes} CASOS)")
    print("==================================================\n")
    
    for caso in casos:
        print(f"[-] Testando ID {caso['id']} | Tipo: {caso['tipo']}")
        
        resposta = gerar_resposta_segura(caso['pergunta'], caso['contexto'])
        
        comportamento_real = "sucesso"
        if "Erro de Segurança" in resposta:
            comportamento_real = "bloqueio_input"
        elif "Bloqueio de Segurança" in resposta:
            comportamento_real = "bloqueio_output"
            
        if comportamento_real == caso['esperado']:
            print(f" ✅ PASSOU (Esperado: {caso['esperado']} | Obtido: {comportamento_real})")
            sucessos += 1
        else:
            print(f" ❌ FALHOU (Esperado: {caso['esperado']} | Obtido: {comportamento_real})")
            print(f"    -> Resposta do sistema: {resposta}")
            falhas += 1
        print("-" * 50)
        
    print("\n==================================================")
    print(" RELATÓRIO FINAL DOS GUARDRAILS")
    print("==================================================")
    print(f" Total Executado: {total_testes}")
    print(f" Taxa de Sucesso: {sucessos}/{total_testes} ({(sucessos/total_testes)*100:.2f}%)")
    print(f" Falhas/Brechas: {falhas}")
    print("==================================================")

if __name__ == "__main__":
    executar_pipeline_de_testes()