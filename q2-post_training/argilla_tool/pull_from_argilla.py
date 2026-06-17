import json
import argparse
import argilla as rg

def parse_args():
    parser = argparse.ArgumentParser(description="Download do dataset revisado do Argilla (Q2)")
    parser.add_argument(
        "--output",
        type=str,
        default="perguntas_docentes_final.json",
        help="Caminho do arquivo JSON de saída limpo e final"
    )
    parser.add_argument(
        "--dataset_name",
        type=str,
        default="docentes_dc_sft",
        help="Nome do dataset criado no Argilla"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    
    # URL e API Key do seu Space no Hugging Face
    api_url = "https://vickminari-docentesdc-dataset-curation.hf.space"
    api_key = "jH4GLbX2A_dVrM0uySuDrRbBgYi8M7azAhRsHUfW2l7kkgFmuKrqD20cbS522bXJh-flnrBD9hgu170bXQ1IQUOcJmGkDWEj5_832dy1Kjc"

    print("=" * 80)
    print("📥 INTEGRAÇÃO COM ARGILLA - BAIXANDO DATASET REVISADO")
    print("=" * 80)
    print(f"Servidor: {api_url}")
    print(f"Dataset no Argilla: {args.dataset_name}")
    print("=" * 80)

    # 1. Inicializar o cliente do Argilla
    print("🔗 Conectando ao servidor Argilla...")
    client = rg.Argilla(api_url=api_url, api_key=api_key)

    # 2. Puxar o dataset
    try:
        dataset = client.datasets(name=args.dataset_name)
        print("✅ Conectado ao dataset com sucesso!")
    except Exception as e:
        print(f"❌ Não foi possível carregar o dataset '{args.dataset_name}': {e}")
        return

    # 3. Iterar e filtrar os registros
    print("🔄 Processando respostas e correções do grupo...")
    final_sft_dataset = []
    approved_count = 0
    rejected_count = 0
    not_annotated_count = 0

    # Iterar pelos registros anotados
    # Nota: Em versões do Argilla 2.x, record.responses contém as respostas fornecidas pelos curadores
    for idx, record in enumerate(dataset.records):
        # Verificar respostas
        # Se houver respostas para a pergunta "status"
        status_responses = record.responses.get("status")
        
        if not status_responses:
            not_annotated_count += 1
            continue
        
        # Obter o valor da primeira resposta (geralmente há 1 resposta por usuário)
        # Se algum usuário marcou como Aprovado
        status_value = status_responses[0].value
        
        if status_value == "Aprovado":
            approved_count += 1
            
            # Pegar os campos originais
            instruction = record.fields["instruction"]
            input_val = record.fields.get("input", "")
            output_val = record.fields["output"]
            
            # Verificar se os anotadores forneceram alguma correção de texto nos campos livres
            corrected_inst_responses = record.responses.get("corrected_instruction")
            corrected_out_responses = record.responses.get("corrected_output")
            
            # Aplicar correções de instrução (pergunta) se houver
            if corrected_inst_responses and corrected_inst_responses[0].value:
                val = corrected_inst_responses[0].value.strip()
                if val:
                    instruction = val
                    
            # Aplicar correções de output (resposta) se houver
            if corrected_out_responses and corrected_out_responses[0].value:
                val = corrected_out_responses[0].value.strip()
                if val:
                    output_val = val

            final_sft_dataset.append({
                "instruction": instruction.strip(),
                "input": input_val.strip(),
                "output": output_val.strip()
            })
            
        elif status_value == "Rejeitar":
            rejected_count += 1
            
    print("\n📈 Estatísticas da Curadoria:")
    print(f"  - Registros Aprovados: {approved_count}")
    print(f"  - Registros Rejeitados: {rejected_count}")
    print(f"  - Não Anotados (Pendente): {not_annotated_count}")
    print(f"  - Total Processado no Loop: {idx + 1 if 'idx' in locals() else 0}")

    if not final_sft_dataset:
        print("\n⚠️  Aviso: Nenhuma pergunta foi aprovada ou anotada ainda.")
        return

    # 4. Salvar o arquivo final compilado
    print(f"\n💾 Salvando dataset final higienizado em: {args.output}")
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(final_sft_dataset, f, indent=2, ensure_ascii=False)

    print("🎉 Exportação final concluída!")
    print(f"📁 Arquivo salvo com sucesso em: {args.output}")
    print(f"📝 Total de perguntas prontas para o Fine-Tuning: {len(final_sft_dataset)}")

if __name__ == "__main__":
    main()
