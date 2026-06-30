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
    
    # Garante que a pasta reports/ exista e define o arquivo como .md
    pasta_reports = os.path.join("..", "reports")
    os.makedirs(pasta_reports, exist_ok=True)
    caminho_relatorio = os.path.join(pasta_reports, "q6_guardrail_evaluation.md")
    
    # Abre o arquivo para escrita limpa de todo o log
    with open(caminho_relatorio, "w", encoding="utf-8") as f:
        
        def log_print(texto=""):
            """Função utilitária para printar no terminal e salvar no arquivo ao mesmo tempo"""
            print(texto)
            f.write(texto + "\n")

        log_print("==================================================")
        log_print(f" INICIANDO VALIDAÇÃO DE GUARDRAILS ({total_testes} CASOS)")
        log_print("==================================================\n")
        
        for caso in casos:
            log_print(f"[-] Testando ID {caso['id']} | Tipo: {caso['tipo']}")
            
            resposta = gerar_resposta_segura(caso['pergunta'], caso['contexto'])
            
            comportamento_real = "sucesso"
            if "Erro de Segurança" in resposta:
                comportamento_real = "bloqueio_input"
            elif "Bloqueio de Segurança" in resposta:
                comportamento_real = "bloqueio_output"
                
            if comportamento_real == caso['esperado']:
                log_print(f" ✅ PASSOU (Esperado: {caso['esperado']} | Obtido: {comportamento_real})")
                sucessos += 1
            else:
                log_print(f" ❌ FALHOU (Esperado: {caso['esperado']} | Obtido: {comportamento_real})")
                log_print(f"    -> Resposta do sistema: {resposta}")
                falhas += 1
            log_print("-" * 50)
            
        log_print("\n==================================================")
        log_print(" RELATÓRIO FINAL DOS GUARDRAILS")
        log_print("==================================================")
        log_print(f" Total Executado: {total_testes}")
        log_print(f" Taxa de Sucesso: {sucessos}/{total_testes} ({(sucessos/total_testes)*100:.2f}%)")
        log_print(f" Falhas/Brechas: {falhas}")
        log_print("==================================================")
        
    print(f"\n[INFO] Avaliação concluída! O relatório completo foi salvo em: {caminho_relatorio}")

if __name__ == "__main__":
    executar_pipeline_de_testes()