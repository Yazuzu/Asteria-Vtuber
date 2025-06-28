import os
from llama_cpp import Llama
import logging
import time
import psutil

logger = logging.getLogger('Modelo')

def carregar_modelo():
    """Carrega o modelo com configurações ultra-otimizadas para baixa latência"""
    modelo_path = "models/Nous-Hermes-2-Mistral-7B-DPO.Q2_K.gguf"

    if not os.path.exists(modelo_path):
        # Tenta baixar automaticamente se não encontrar
        try:
            logger.warning("Modelo não encontrado. Baixando...")
            os.system('wget https://gpt4all.io/models/gguf/nous-hermes-2-mistral-7b-dpo.Q2_K.gguf -P models/')
        except Exception as e:
            raise FileNotFoundError(f"Falha ao baixar modelo: {str(e)}")

    logger.info("⏳ Carregando modelo com configurações de alto desempenho...")

    # Configurações para máxima velocidade
    model = Llama(
        model_path=modelo_path,
        n_ctx=1024,                  # Contexto reduzido
        n_threads=max(psutil.cpu_count(logical=False),  # Usa apenas cores físicos
        n_gpu_layers=0,              # CPU-only para melhor compatibilidade
        n_batch=512,                 # Batch maior para eficiência
        use_mmap=True,               # Uso de mmap para carregamento rápido
        use_mlock=False,             # Desativar mlock para evitar problemas
        offload_kqv=True,            # Descarregar camadas críticas
        main_gpu=0,                  # GPU principal
        tensor_split=[0],            # Alocação de VRAM
        seed=42,                     # Seed fixa para consistência
        low_vram=True,               # Modo de baixo consumo de VRAM
        verbose=False                # Sem logs internos
    ))

    # Pré-aquecimento eficiente
    logger.info("🔥 Pré-aquecendo para streaming...")
    start = time.time()
    warmup_prompt = "Pre-aquecendo " * 20

    # Pré-aquecimento em 2 estágios
    for _ in range(3):
        model.create_completion(warmup_prompt, max_tokens=1)

    logger.info(f"⚡ Pré-aquecimento concluído em {time.time() - start:.2f}s")

    return model

# Teste de desempenho integrado
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    try:
        model = carregar_modelo()
        prompt = "Qual é o significado da vida?"

        # Teste de velocidade
        start = time.time()
        response = model.create_completion(prompt, max_tokens=50, temperature=0.7)
        elapsed = time.time() - start

        tokens = len(response['choices'][0]['text'].split())
        logger.info(f"⚡ Tokens gerados: {tokens}")
        logger.info(f"⏱️ Tempo total: {elapsed:.2f}s")
        logger.info(f"📝 Resposta: {response['choices'][0]['text']}")

        # Teste de streaming
        logger.info("\n🚀 Teste de streaming:")
        start = time.time()
        stream = model.create_completion(prompt, max_tokens=50, stream=True)
        first_token_time = None
        for i, chunk in enumerate(stream):
            token = chunk['choices'][0]['text']
            if i == 0:
                first_token_time = time.time() - start
            print(token, end='', flush=True)

        logger.info(f"\n\n⏱️ Primeiro token em {first_token_time:.2f}s")
        logger.info(f"⏱️ Tempo total: {time.time() - start:.2f}s")

    except Exception as e:
        logger.error(f"Erro no teste: {str(e)}")
