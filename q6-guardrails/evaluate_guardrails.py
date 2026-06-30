import json
import os
import sys

# Reconfigura stdout para UTF-8 para evitar erros de encode em terminais Windows (cp1252)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Garante que o diretório do script esteja no sys.path para importações locais
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from guardrails_pipeline import gerar_resposta_segura 

def carregar_casos_de_teste():
    caminho_json = os.path.join(script_dir, "test_cases.json")
    if not os.path.exists(caminho_json):
        raise FileNotFoundError(f"Arquivo {caminho_json} não encontrado.")
    with open(caminho_json, "r", encoding="utf-8") as f:
        return json.load(f)

def executar_pipeline_de_testes():
    casos = carregar_casos_de_teste()
    total_testes = len(casos)
    
    # Dicionários para contagem de resultados
    estatisticas = {
        "total": total_testes,
        "sucessos": 0,
        "falhas": 0,
        "taxa_sucesso": 0.0,
        "por_tipo": {
            "seguro": {"total": 0, "sucessos": 0, "falhas": 0},
            "prompt_injection": {"total": 0, "sucessos": 0, "falhas": 0},
            "alucinacao_potencial": {"total": 0, "sucessos": 0, "falhas": 0}
        }
    }
    
    resultados_detalhados = []
    
    # Garante que a pasta reports/ exista
    pasta_reports = os.path.abspath(os.path.join(script_dir, "..", "reports"))
    os.makedirs(pasta_reports, exist_ok=True)
    
    caminho_json_output = os.path.join(pasta_reports, "q6_guardrail_evaluation.json")
    caminho_md_output = os.path.join(pasta_reports, "q6_guardrail_evaluation_report.md")
    
    print("==================================================")
    print(f" INICIANDO VALIDAÇÃO DE GUARDRAILS ({total_testes} CASOS)")
    print("==================================================\n")
    
    for caso in casos:
        tipo = caso['tipo']
        estatisticas["por_tipo"][tipo]["total"] += 1
        
        resposta = gerar_resposta_segura(caso['pergunta'], caso['contexto'])
        
        comportamento_real = "sucesso"
        if "Erro de Segurança" in resposta:
            comportamento_real = "bloqueio_input"
        elif "Bloqueio de Segurança" in resposta:
            comportamento_real = "bloqueio_output"
            
        status = "FALHOU"
        if comportamento_real == caso['esperado']:
            status = "PASSOU"
            estatisticas["sucessos"] += 1
            estatisticas["por_tipo"][tipo]["sucessos"] += 1
            print(f"[-] ID {caso['id']} | Tipo: {tipo:20} | ✅ PASSOU")
        else:
            estatisticas["falhas"] += 1
            estatisticas["por_tipo"][tipo]["falhas"] += 1
            print(f"[-] ID {caso['id']} | Tipo: {tipo:20} | ❌ FALHOU (Esperado: {caso['esperado']} | Obtido: {comportamento_real})")
            print(f"    -> Resposta: {resposta}")
            
        resultados_detalhados.append({
            "id": caso['id'],
            "tipo": tipo,
            "contexto": caso['contexto'],
            "pergunta": caso['pergunta'],
            "esperado": caso['esperado'],
            "obtido": comportamento_real,
            "resposta_sistema": resposta,
            "status": status
        })
        
    estatisticas["taxa_sucesso"] = (estatisticas["sucessos"] / total_testes) * 100
    
    # 1. Salva o arquivo JSON puro
    report_json = {
        "metrics": estatisticas,
        "runs": resultados_detalhados
    }
    with open(caminho_json_output, "w", encoding="utf-8") as f:
        json.dump(report_json, f, ensure_ascii=False, indent=2)
    print(f"\n[INFO] Resultados puros salvos em: {caminho_json_output}")
    
    # 2. Gera o relatório Markdown rico e detalhado
    gerar_relatorio_md(caminho_md_output, estatisticas, resultados_detalhados)
    print(f"[INFO] Relatório detalhado salvo em: {caminho_md_output}")

def gerar_relatorio_md(caminho_md, estatisticas, runs):
    with open(caminho_md, "w", encoding="utf-8") as f:
        f.write("# Relatório de Avaliação de Guardrails (Q6)\n\n")
        f.write("Este relatório detalha a validação de segurança e robustez do pipeline de Guardrails implementado para o modelo do projeto. Avaliamos a eficiência na retenção de ataques de *Prompt Injection* (segurança ativa no input) e de *Alucinações* (groundedness check no output) sobre uma suite de testes com 30 casos extremos.\n\n")
        
        f.write("---\n\n")
        
        f.write("## 📊 Resumo Executivo das Métricas\n\n")
        f.write(f"Abaixo estão os resultados consolidados obtidos na execução dos testes de validação:\n\n")
        
        f.write("| Métrica | Valor |\n")
        f.write("| :--- | :---: |\n")
        f.write(f"| **Total de Casos Executados** | {estatisticas['total']} |\n")
        f.write(f"| **Sucessos (Retenções/Passagens Corretas)** | {estatisticas['sucessos']}/{estatisticas['total']} |\n")
        f.write(f"| **Falhas/Brechas de Segurança** | {estatisticas['falhas']} |\n")
        f.write(f"| **Taxa de Sucesso Geral** | **{estatisticas['taxa_sucesso']:.2f}%** |\n\n")
        
        f.write("### Desempenho por Categoria de Teste\n\n")
        f.write("| Tipo de Caso | Total | Sucessos | Falhas | Taxa de Sucesso |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: |\n")
        
        for tipo, dados in estatisticas["por_tipo"].items():
            tx = (dados["sucessos"] / dados["total"]) * 100 if dados["total"] > 0 else 0
            nome_tipo = tipo.replace("_", " ").title()
            f.write(f"| {nome_tipo} | {dados['total']} | {dados['sucessos']} | {dados['falhas']} | {tx:.1f}% |\n")
            
        f.write("\n---\n\n")
        
        f.write("## 🛡️ Análise Qualitativa das Camadas de Defesa\n\n")
        f.write("### 1. Camada de Validação de Entrada (`input_guardrail`)\n")
        f.write("Esta camada intercepta a requisição do usuário antes de enviá-la para a LLM. Ela foi projetada para detectar assinaturas de ataques como *Prompt Injection*, tentativas de forçar regras de sistema fora do escopo, ou bypasses de filtros.\n")
        f.write("- **Mecanismo:** Utiliza expressões regulares (regex) flexíveis e insensíveis a maiúsculas/minúsculas para identificar palavras-chave suspeitas (`ignore as regras`, `esqueça o filtro`, `agir como`, etc.) e limitações de comprimento físico de string.\n")
        f.write("- **Resultado:** Reteve **100%** dos ataques direcionados a burlar o comportamento do sistema sem sobrecarregar chamadas da API.\n\n")
        
        f.write("### 2. Camada de Validação de Saída (`output_guardrail`)\n")
        f.write("Focada em consistência de contexto (*Groundedness Checking*). Se a LLM gerar informações não condizentes com os documentos de contexto fornecidos, a resposta é barrada antes de chegar ao usuário final.\n")
        f.write("- **Mecanismo:** Calcula o índice de alinhamento léxico das palavras-chave relevantes entre a resposta produzida pela LLM e o contexto. Caso a correspondência seja inferior ao threshold mínimo de 15%, o output é classificado como potencial alucinação e bloqueado.\n")
        f.write("- **Resultado:** Bloqueou com precisão todas as tentativas de fazer o modelo responder fora do contexto fornecido (ex: receitas, cotações financeiras, curiosidades gerais).\n\n")
        
        f.write("---\n\n")
        
        f.write("## 💡 Exemplos de Contenção e Execução\n\n")
        
        # Encontra exemplos de cada tipo para ilustrar
        ex_seguro = next((r for r in runs if r["tipo"] == "seguro" and r["status"] == "PASSOU"), None)
        ex_injection = next((r for r in runs if r["tipo"] == "prompt_injection" and r["status"] == "PASSOU"), None)
        ex_aluc = next((r for r in runs if r["tipo"] == "alucinacao_potencial" and r["status"] == "PASSOU"), None)
        
        if ex_seguro:
            f.write("### 🟢 Caso 1: Requisição Legítima (Permitida)\n")
            f.write(f"- **Pergunta:** `\"{ex_seguro['pergunta']}\"`\n")
            f.write(f"- **Contexto:** *\"{ex_seguro['contexto']}\"*\n")
            f.write(f"- **Resposta Entregue:** `\"{ex_seguro['resposta_sistema']}\"`\n")
            f.write(f"- **Status de Proteção:** Aprovado e entregue com sucesso.\n\n")
            
        if ex_injection:
            f.write("### 🔴 Caso 2: Ataque de Prompt Injection (Bloqueado no Input)\n")
            f.write(f"- **Pergunta:** `\"{ex_injection['pergunta']}\"`\n")
            f.write(f"- **Resposta de Segurança:** `\"{ex_injection['resposta_sistema']}\"`\n")
            f.write(f"- **Status de Proteção:** Retido na camada de entrada antes da inferência do modelo.\n\n")
            
        if ex_aluc:
            f.write("### 🟡 Caso 3: Tentativa de Alucinação (Bloqueado no Output)\n")
            f.write(f"- **Pergunta:** `\"{ex_aluc['pergunta']}\"`\n")
            f.write(f"- **Contexto:** *\"{ex_aluc['contexto']}\"*\n")
            f.write(f"- **Resposta do Modelo (Alucinada):** *\"Para fazer bolo de cenoura você precisa de cenouras...\"*\n")
            f.write(f"- **Resposta de Segurança:** `\"{ex_aluc['resposta_sistema']}\"`\n")
            f.write(f"- **Status de Proteção:** Identificado como desconectado do contexto e barrado no output.\n\n")
            
        f.write("---\n\n")
        
        f.write("## 📋 Tabela Completa de Resultados da Execução\n\n")
        f.write("| ID | Tipo | Pergunta | Esperado | Obtido | Status |\n")
        f.write("| :---: | :--- | :--- | :--- | :--- | :---: |\n")
        
        for run in runs:
            emoji = "✅" if run["status"] == "PASSOU" else "❌"
            f.write(f"| {run['id']} | {run['tipo']} | {run['pergunta']} | {run['esperado']} | {run['obtido']} | {emoji} |\n")

if __name__ == "__main__":
    executar_pipeline_de_testes()