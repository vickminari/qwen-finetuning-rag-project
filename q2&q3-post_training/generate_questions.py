import os
import json
import random
import time
import argparse
import requests
from collections import defaultdict

def parse_args():
    parser = argparse.ArgumentParser(
        description="Gerador de perguntas e respostas sintéticas (Q2 - Pós-Treino) usando LLM local"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="vickminari/docentesDC",
        help="Nome do repositório do Hugging Face ou caminho para o arquivo local"
    )
    parser.add_argument(
        "--backend",
        type=str,
        choices=["ollama", "vllm", "openai"],
        default="ollama",
        help="Backend de LLM local a ser utilizado"
    )
    parser.add_argument(
        "--api_url",
        type=str,
        default=None,
        help="URL base da API (ex: http://localhost:11434 para Ollama ou http://localhost:8000 para vLLM)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="qwen3.5:9b",
        help="Nome do modelo conforme configurado no backend (ex: qwen3.5:9b, qwen3.5:2b, qwen2.5:7b)"
    )
    parser.add_argument(
        "--target_count",
        type=int,
        default=1000,
        help="Quantidade total de perguntas a serem geradas"
    )
    parser.add_argument(
        "--questions_per_chunk",
        type=int,
        default=2,
        help="Quantidade de perguntas a serem solicitadas por chunk de texto"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="perguntas_docentes.json",
        help="Arquivo JSON final contendo todas as perguntas geradas"
    )
    parser.add_argument(
        "--checkpoint_file",
        type=str,
        default="perguntas_docentes_checkpoint.jsonl",
        help="Arquivo JSONL para salvar o progresso incremental"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Semente aleatória para reprodutibilidade da amostragem"
    )
    parser.add_argument(
        "--chunk_size",
        type=int,
        default=2500,
        help="Tamanho do chunk de caracteres para enviar ao LLM"
    )
    return parser.parse_args()

def load_data(dataset_source):
    """
    Carrega os dados. Tenta primeiro via Hugging Face.
    Se falhar ou for um arquivo local, tenta ler o arquivo local JSONL ou Parquet.
    """
    # Se o argumento parecer um arquivo local que existe
    if os.path.exists(dataset_source):
        return load_local_file(dataset_source)

    # Tentar Hugging Face
    try:
        print(f"📥 Carregando dataset do Hugging Face '{dataset_source}'...")
        from datasets import load_dataset
        dataset = load_dataset(dataset_source, split="train")
        print(f"✅ Dataset carregado com sucesso do Hugging Face! Registros: {len(dataset)}")
        return [{"text": row["text"], "nome_professor": row["nome_professor"]} for row in dataset]
    except Exception as e:
        print(f"⚠️  Falha ao carregar do Hugging Face ({e}). Tentando caminhos locais padrão...")

    # Tentar caminhos locais padrão relativos ao script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.join(script_dir, "../../dados_docentes/docentesDC/docentesDC.jsonl"),
        os.path.join(script_dir, "../../dados_docentes/docentesDC/docentesDC.parquet"),
        os.path.join(script_dir, "docentesDC.jsonl"),
        "dados_docentes/docentesDC/docentesDC.jsonl",
        "docentesDC.jsonl"
    ]

    for path in possible_paths:
        if os.path.exists(path):
            print(f"📂 Arquivo local encontrado: {path}")
            return load_local_file(path)

    raise FileNotFoundError(
        "Não foi possível carregar o dataset do Hugging Face nem encontrar arquivos locais. "
        "Verifique se o arquivo docentesDC.jsonl está no diretório correto ou configure o parâmetro --dataset."
    )

def load_local_file(path):
    """
    Carrega dados de um arquivo local JSONL ou Parquet.
    """
    print(f"📦 Carregando dados do arquivo local: {path}")
    if path.endswith(".jsonl"):
        data = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
        print(f"✅ Carregados {len(data)} registros do JSONL local.")
        return data
    elif path.endswith(".parquet"):
        try:
            import pandas as pd
            df = pd.read_parquet(path)
            data = df.to_dict(orient="records")
            print(f"✅ Carregados {len(data)} registros do Parquet local.")
            return data
        except ImportError:
            raise ImportError("Instale o pandas (pip install pandas pyarrow) para ler arquivos Parquet.")
    else:
        raise ValueError("Formato de arquivo local não suportado. Use .jsonl ou .parquet.")

def clean_and_chunk_text(text, chunk_size=2500):
    """
    Divide o texto em chunks de tamanho aproximado para enviar ao LLM.
    Ignora partes vazias ou excesso de espaços.
    """
    text = text.strip()
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + chunk_size])
        start += chunk_size - 200 # Overlap de 200 caracteres para manter o contexto
    return chunks

def call_local_llm(backend, api_url, model, system_prompt, user_prompt):
    """
    Envia a requisição para o LLM local usando o backend configurado e retorna o conteúdo gerado.
    Tenta primeiro usar a biblioteca openai com reasoning_effort='none' e temperature=0.1,
    e cai para requisições HTTP normais (requests) se necessário.
    """
    # Resolver URLs padrão se não especificadas
    if not api_url:
        if backend == "ollama":
            api_url = "http://localhost:11434"
        else:
            api_url = "http://localhost:8000"

    # Tenta usar a biblioteca oficial da OpenAI (se instalada)
    try:
        from openai import OpenAI
        base_url = api_url.rstrip('/')
        # Ollama expõe a API compatível com OpenAI em /v1
        if backend == "ollama" and not base_url.endswith("/v1"):
            base_url = f"{base_url}/v1"

        client = OpenAI(base_url=base_url, api_key="ollama" if backend == "ollama" else "dummy")
        
        # Adicionar parâmetros extras para desativar o reasoning do Qwen3.5 se compatível
        kwargs = {}
        if backend in ["ollama", "vllm", "openai"]:
            kwargs["reasoning_effort"] = "none"

        response = client.chat.completions.create(
            model=model,
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            **kwargs
        )
        return response.choices[0].message.content

    except Exception as e_openai:
        # Fallback 1: Usar a API compatível OpenAI via requests
        base_url = api_url.rstrip('/')
        endpoint = f"{base_url}/v1/chat/completions"
        
        # Se for o Ollama, certificar que a URL tem /v1
        if backend == "ollama" and not base_url.endswith("/v1"):
            endpoint = f"{base_url}/v1/chat/completions"
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
            "reasoning_effort": "none"
        }

        try:
            response = requests.post(endpoint, json=payload, timeout=60)
            response.raise_for_status()
            res_json = response.json()
            return res_json["choices"][0]["message"]["content"]
        except Exception as e_req:
            # Fallback 2: Tentar a API de chat nativa do Ollama (/api/chat) se o backend for ollama
            if backend == "ollama":
                native_endpoint = f"{base_url.replace('/v1', '')}/api/chat"
                native_payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0.1
                    }
                }
                try:
                    response = requests.post(native_endpoint, json=native_payload, timeout=60)
                    response.raise_for_status()
                    return response.json()["message"]["content"]
                except Exception as e_native:
                    print(f"❌ Todos os métodos de chamada da API falharam. Erro original (OpenAI Client): {e_openai}. Erro HTTP: {e_native}")
            else:
                print(f"❌ Falha ao chamar a API: {e_req}")
            return None

def parse_llm_json(raw_text):
    """
    Tenta analisar a saída do LLM como JSON.
    Trata delimitadores de markdown comuns e diferentes estruturas de objetos.
    """
    if not raw_text:
        return None
    
    clean_text = raw_text.strip()
    
    # Remover tags de bloco de código markdown ```json se presentes
    if clean_text.startswith("```"):
        # Remove a primeira linha
        lines = clean_text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        clean_text = "\n".join(lines).strip()

    try:
        data = json.loads(clean_text)
        
        # O modelo pode ter retornado {"questions": [...]} ou diretamente [...]
        if isinstance(data, dict):
            if "questions" in data:
                return data["questions"]
            elif "perguntas" in data:
                return data["perguntas"]
            else:
                # Se for um dicionário único de perguntas, pode ser um erro, mas vamos verificar
                # se parece com uma única pergunta e envelopá-la em lista
                if "instruction" in data:
                    return [data]
        elif isinstance(data, list):
            return data
            
    except Exception as e:
        print(f"⚠️  Erro ao decodificar JSON: {e}. Conteúdo bruto recebido:\n{raw_text[:200]}...")
        
    return None

def main():
    args = parse_args()
    random.seed(args.seed)

    print("=" * 80)
    print("🤖 GERADOR DE PERGUNTAS E RESPOSTAS ACADÊMICAS (Q2)")
    print("=" * 80)
    print(f"Backend: {args.backend}")
    print(f"Modelo: {args.model}")
    print(f"Meta de perguntas: {args.target_count}")
    print("=" * 80)

    # 1. Carregar dados
    try:
        raw_data = load_data(args.dataset)
    except Exception as e:
        print(f"❌ Erro crítico ao carregar dados: {e}")
        return

    # 2. Agrupar documentos por professor para distribuição equilibrada
    prof_docs = defaultdict(list)
    for idx, doc in enumerate(raw_data):
        prof = doc.get("nome_professor", "Desconhecido").strip()
        text = doc.get("text", "").strip()
        if text and len(text) > 100: # Ignorar textos extremamente curtos
            prof_docs[prof].append({"doc_id": idx, "text": text})

    print(f"\n📊 Distribuição de documentos por professor:")
    for prof, docs in sorted(prof_docs.items()):
        print(f"  - {prof}: {len(docs)} documentos")

    # 3. Preparar a fila round-robin de chunks por professor
    # Para cada professor, vamos embaralhar seus documentos de forma reprodutível
    professores = list(prof_docs.keys())
    for prof in professores:
        random.shuffle(prof_docs[prof])

    # Construir uma fila de chunks. Cada elemento é (professor, doc_id, chunk_idx, chunk_text)
    sampling_queue = []
    # Usamos um cursor para rodar round-robin pelos professores
    prof_cursors = {p: 0 for p in professores}
    
    # Continuamos até termos chunks suficientes para trabalhar
    # Cada documento será dividido em chunks. Vamos processar 1 chunk por vez de cada professor
    active_profs = list(professores)
    while active_profs:
        for prof in list(active_profs):
            cursor = prof_cursors[prof]
            if cursor >= len(prof_docs[prof]):
                active_profs.remove(prof)
                continue
            
            doc = prof_docs[prof][cursor]
            chunks = clean_and_chunk_text(doc["text"], args.chunk_size)
            
            # Adiciona apenas o primeiro chunk para diversificar mais (depois se faltar podemos pegar outros)
            # Mas para garantir bastante dados, vamos adicionar os chunks desse documento
            for c_idx, chunk_text in enumerate(chunks[:2]): # Limita a no máximo 2 chunks por documento para manter diversidade
                sampling_queue.append({
                    "professor": prof,
                    "doc_id": doc["doc_id"],
                    "chunk_idx": c_idx,
                    "text": chunk_text
                })
            
            prof_cursors[prof] += 1

    print(f"\n📦 Fila de amostragem criada com {len(sampling_queue)} chunks de texto prontos.")

    # Embaralhar a fila de chunks final para misturar os professores no progresso
    random.shuffle(sampling_queue)

    # 4. Ler progresso existente (Checkpoint)
    processed_chunks = set()
    all_generated_questions = []

    if os.path.exists(args.checkpoint_file):
        print(f"\n🔄 Checkpoint encontrado: '{args.checkpoint_file}'. Carregando progresso...")
        with open(args.checkpoint_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    prof = item.get("professor")
                    doc_id = item.get("doc_id")
                    chunk_idx = item.get("chunk_idx")
                    questions = item.get("questions", [])
                    
                    processed_chunks.add((prof, doc_id, chunk_idx))
                    all_generated_questions.extend(questions)
        print(f"✅ Progresso retomado. Já temos {len(all_generated_questions)} perguntas geradas de {len(processed_chunks)} chunks.")
    else:
        print("\n🆕 Nenhum checkpoint encontrado. Iniciando do zero.")

    # Prompts
    system_prompt = (
        "Você é um assistente acadêmico especialista em computação e geração de dados sintéticos "
        "de alta qualidade para ajuste fino (fine-tuning) de LLMs."
    )

    # 5. Loop de geração
    total_generated = len(all_generated_questions)
    
    if total_generated >= args.target_count:
        print(f"\n🎉 Meta de {args.target_count} perguntas já foi atingida!")
    else:
        print(f"\n🚀 Iniciando geração de perguntas. Meta restante: {args.target_count - total_generated}...")
        
        for idx, item in enumerate(sampling_queue):
            if total_generated >= args.target_count:
                break
                
            prof = item["professor"]
            doc_id = item["doc_id"]
            chunk_idx = item["chunk_idx"]
            chunk_text = item["text"]

            # Pular se já processado no checkpoint
            if (prof, doc_id, chunk_idx) in processed_chunks:
                continue

            print(f"\n[Chunk {idx+1}/{len(sampling_queue)}] Gerando para Professor: {prof} (Doc: {doc_id}, Chunk: {chunk_idx})")
            
            user_prompt = (
                f"Você deve ler atentamente o texto técnico abaixo:\n\n"
                f"\"\"\"\n{chunk_text}\n\"\"\"\n\n"
                f"Sua tarefa é gerar exatamente {args.questions_per_chunk} perguntas e respostas técnicas de alta qualidade "
                f"baseadas estritamente nas informações científicas/técnicas do texto.\n\n"
                f"Diretrizes Críticas para a Geração:\n"
                f"1. **Perguntas Autocontidas e Técnicas**: Cada pergunta deve ser independente e fazer sentido completo "
                f"por si só, sem depender da leitura prévia do texto original. Evite perguntas genéricas ou sobre a estrutura do documento.\n"
                f"2. **PROIBIDO referenciar a fonte ou autor**: NÃO use expressões como 'no texto extraído', 'segundo o texto', 'nas notas de aula', "
                f"'nos slides', 'no artigo', 'do professor', nem cite nomes de professores ou universidades na pergunta ou na resposta.\n"
                f"3. **Uso do campo 'input'**: \n"
                f"   - Se a pergunta for puramente conceitual, o campo 'input' deve ser obrigatoriamente uma string vazia (\"\").\n"
                f"   - O campo 'input' só deve ser preenchido se for necessário fornecer um fragmento de código, "
                f"tabela ou dado específico contido no texto para que a pergunta faça sentido. Exemplo: se a instrução for "
                f"'Qual a função deste trecho de código?', o código deve ser colocado no campo 'input'.\n"
                f"4. **Qualidade Técnica**: Foque em conceitos de computação, engenharia de software, banco de dados, LGPD, algoritmos ou redes de computadores presentes no texto.\n"
                f"5. **Idioma**: As perguntas e respostas devem ser em português do Brasil.\n"
                f"6. **Formato JSON**: A saída DEVE ser um objeto JSON válido contendo uma chave \"questions\" com a lista de perguntas:\n"
                f"{{\n"
                f"  \"questions\": [\n"
                f"    {{\"instruction\": \"pergunta técnica autocontida...\", \"input\": \"\", \"output\": \"resposta conceitual...\"}},\n"
                f"    ...\n"
                f"  ]\n"
                f"}}\n"
            )

            # Chamar a API local
            raw_response = call_local_llm(args.backend, args.api_url, args.model, system_prompt, user_prompt)
            
            if not raw_response:
                print("⚠️  Sem resposta do LLM. Pulando para o próximo chunk...")
                time.sleep(2)
                continue

            # Parsear JSON
            questions = parse_llm_json(raw_response)
            
            if not questions:
                print("⚠️  Falha ao analisar a resposta JSON do LLM. Pulando...")
                time.sleep(1)
                continue

            # Validar estrutura básica de cada pergunta
            valid_questions = []
            for q in questions:
                if isinstance(q, dict) and "instruction" in q and "output" in q:
                    # Preservar o campo 'input' gerado, ou usar string vazia como fallback
                    input_val = q.get("input", "")
                    if input_val is None:
                        input_val = ""
                    valid_questions.append({
                        "instruction": q["instruction"].strip(),
                        "input": str(input_val).strip(),
                        "output": q["output"].strip()
                    })

            if not valid_questions:
                print("⚠️  Nenhuma pergunta válida encontrada na resposta. Pulando...")
                continue

            # Salvar no progresso em memória
            all_generated_questions.extend(valid_questions)
            total_generated = len(all_generated_questions)
            processed_chunks.add((prof, doc_id, chunk_idx))

            # Gravar no arquivo de checkpoint incremental imediatamente
            checkpoint_data = {
                "professor": prof,
                "doc_id": doc_id,
                "chunk_idx": chunk_idx,
                "questions": valid_questions
            }
            with open(args.checkpoint_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(checkpoint_data, ensure_ascii=False) + "\n")

            print(f"✅ Sucesso! Geradas {len(valid_questions)} perguntas. Total acumulado: {total_generated}/{args.target_count}")
            
            # Pequeno delay para evitar sobrecarregar a API local
            time.sleep(0.5)

    # 6. Salvar o arquivo final compilado
    print(f"\n💾 Compilando {len(all_generated_questions)} perguntas para o arquivo final '{args.output}'...")
    
    # Se gerou mais que o alvo, podemos truncar para ficar exatamente com target_count se desejado,
    # mas geralmente ter um pouco mais de 1000 é bom. Vamos manter todas as geradas.
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(all_generated_questions, f, indent=2, ensure_ascii=False)

    print(f"🎉 Processo concluído com sucesso!")
    print(f"📁 Arquivo final salvo em: {os.path.abspath(args.output)}")
    print(f"📝 Total de perguntas geradas: {len(all_generated_questions)}")

if __name__ == "__main__":
    main()
