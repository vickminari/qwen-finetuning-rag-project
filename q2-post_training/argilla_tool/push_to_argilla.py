import os
import json
import argparse
import argilla as rg

def parse_args():
    parser = argparse.ArgumentParser(description="Upload de perguntas e respostas para o Argilla (Q2)")
    parser.add_argument(
        "--file",
        type=str,
        default="perguntas_docentes.json",
        help="Caminho do arquivo JSON final das perguntas"
    )
    parser.add_argument(
        "--checkpoint_file",
        type=str,
        default="perguntas_docentes_checkpoint.jsonl",
        help="Caminho do arquivo JSONL de checkpoint caso queira subir progresso parcial"
    )
    parser.add_argument(
        "--dataset_name",
        type=str,
        default="docentes_dc_sft",
        help="Nome do dataset a ser criado no Argilla"
    )
    return parser.parse_args()

def load_questions(json_path, jsonl_path):
    """
    Carrega as perguntas do arquivo JSON compilado.
    Se não existir, tenta ler as perguntas parciais do arquivo JSONL do checkpoint.
    """
    if os.path.exists(json_path):
        print(f"📂 Carregando perguntas compiladas do arquivo: {json_path}")
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    elif os.path.exists(jsonl_path):
        print(f"📂 Arquivo compilado não encontrado. Carregando perguntas parciais do checkpoint: {jsonl_path}")
        questions = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    questions.extend(item.get("questions", []))
        return questions
    else:
        raise FileNotFoundError(f"Nenhum arquivo encontrado em '{json_path}' ou '{jsonl_path}'.")

def main():
    args = parse_args()
    
    # URL e API Key do seu Space no Hugging Face
    api_url = "https://vickminari-docentesdc-dataset-curation.hf.space"
    api_key = "jH4GLbX2A_dVrM0uySuDrRbBgYi8M7azAhRsHUfW2l7kkgFmuKrqD20cbS522bXJh-flnrBD9hgu170bXQ1IQUOcJmGkDWEj5_832dy1Kjc"

    print("=" * 80)
    print("🚀 INTEGRAÇÃO COM ARGILLA - SUBINDO DATASET PARA CURADORIA")
    print("=" * 80)
    print(f"Servidor: {api_url}")
    print(f"Dataset no Argilla: {args.dataset_name}")
    print("=" * 80)

    # 1. Carregar as perguntas geradas
    try:
        questions = load_questions(args.file, args.checkpoint_file)
        print(f"✅ Carregadas {len(questions)} perguntas para envio.")
    except Exception as e:
        print(f"❌ Erro ao carregar perguntas: {e}")
        return

    # 2. Inicializar o cliente do Argilla
    print("\n🔗 Conectando ao servidor Argilla...")
    client = rg.Argilla(api_url=api_url, api_key=api_key)

    # 3. Definir as configurações do Dataset (Focado em SFT)
    # Define as orientações de curadoria para o grupo
    guidelines = (
        "Instruções para Curadoria Humana (Grupo de 4 Pessoas):\n\n"
        "1. Analise se a pergunta (instruction) é autocontida e técnica.\n"
        "2. Certifique-se de que NÃO há referências como 'no texto extraído', 'segundo as notas de aula' ou nomes dos professores na pergunta/resposta.\n"
        "3. O campo 'input' deve ficar vazio, a menos que contenha um trecho de código essencial para responder à pergunta.\n"
        "4. Avalie a resposta (output). Ela deve ser precisa e factual.\n"
        "5. Marque a pergunta como 'Aprovada' ou 'Rejeitada'. Se precisar de pequenos ajustes, faça as correções nos campos de texto adicionais e marque como 'Aprovada'."
    )

    settings = rg.Settings(
        guidelines=guidelines,
        fields=[
            rg.TextField(name="instruction", title="Instrução / Pergunta", use_markdown=True),
            rg.TextField(name="input", title="Contexto / Input (Ex: Código)", required=False, use_markdown=True),
            rg.TextField(name="output", title="Resposta Esperada / Output", use_markdown=True),
        ],
        questions=[
            rg.LabelQuestion(
                name="status",
                title="Avaliação da Pergunta",
                labels=["Aprovado", "Rejeitar"],
                required=True
            ),
            rg.TextQuestion(
                name="corrected_instruction",
                title="Correção da Pergunta (Opcional - preencha se quiser editar)",
                required=False
            ),
            rg.TextQuestion(
                name="corrected_output",
                title="Correção da Resposta (Opcional - preencha se quiser editar)",
                required=False
            )
        ]
    )

    # 4. Criar o Dataset no Argilla
    # Se já existir, podemos alertar ou remover (vamos criar com o nome especificado)
    try:
        dataset = rg.Dataset(
            name=args.dataset_name,
            settings=settings
        )
        print("🛠️  Criando dataset no servidor Argilla...")
        dataset.create()
        print("✅ Dataset criado com sucesso no servidor!")
    except Exception as e:
        print(f"⚠️  Dataset já existe ou ocorreu um erro: {e}")
        print("Tentando carregar o dataset existente para adicionar registros...")
        try:
            dataset = client.datasets(name=args.dataset_name)
        except Exception as err:
            print(f"❌ Não foi possível obter o dataset existente: {err}")
            return

    # 5. Criar registros do Argilla
    print("\n📦 Formatando registros para o Argilla...")
    records = []
    for q in questions:
        records.append(
            rg.Record(
                fields={
                    "instruction": q["instruction"],
                    "input": q.get("input", ""),
                    "output": q["output"]
                }
            )
        )

    # 6. Upload dos registros
    print(f"📤 Enviando {len(records)} registros para o Argilla (isso pode levar alguns instantes)...")
    try:
        dataset.records.log(records)
        print("\n" + "=" * 80)
        print("🎉 UPLOAD CONCLUÍDO COM SUCESSO!")
        print("=" * 80)
        print(f"🔗 Acesse a interface web para começar a curadoria:")
        print(f"👉 {api_url}")
        print("=" * 80)
    except Exception as e:
        print(f"❌ Erro ao enviar registros: {e}")

if __name__ == "__main__":
    main()
