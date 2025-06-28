import discord
from discord.ext import commands
import asyncio
import os
from llama_cpp import Llama
from persona import Asteria
import time
from langdetect import detect, LangDetectException
import logging
import json
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('Astéria')

# Configurações
TOKEN = os.getenv("DISCORD_BOT_TOKEN") or "DISCORD_TOKEN_REMOVIDO"
CRIADOR_ID = int(os.getenv("CRIADOR_ID", "766317071369109544"))
MAX_HISTORY = 2
MAX_TOKENS = 180
TEMPERATURE = 0.72
TIMEOUT_GENERATION = 20.0

# Carregar modelo
model = None
def load_model():
    global model
    if model is None:
        logger.info("⏳ Carregando modelo de linguagem...")
        model = Llama(
            model_path="models/Nous-Hermes-2-Mistral-7B-DPO.Q3_K_M.gguf",
            n_ctx=2048,
            n_threads=8,
            n_gpu_layers=40 if os.getenv('USE_GPU') == '1' else 0,
            verbose=False
        )
        logger.info("✅ Modelo carregado com sucesso!")
    return model

# Intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
asteria = Asteria()

# Histórico em memória e sistema de logs
user_history = {}
message_logs = []

def log_message(user_id: int, username: str, content: str, response: str = "", elapsed: float = 0):
    """Registra mensagem detalhada para análise"""
    timestamp = datetime.now().isoformat()
    entry = {
        "timestamp": timestamp,
        "user_id": user_id,
        "username": username,
        "input": content,
        "response": response,
        "response_time": elapsed,
        "emotional_state": asteria.estado_emocional.copy()
    }
    message_logs.append(entry)

    # Salva periodicamente em arquivo
    if len(message_logs) >= 5:
        save_logs_to_file()

def save_logs_to_file():
    """Salva logs em arquivo JSON"""
    if not message_logs:
        return

    try:
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        filename = f"{log_dir}/conversas_{datetime.now().strftime('%Y%m%d')}.jsonl"

        with open(filename, "a", encoding="utf-8") as f:
            for entry in message_logs:
                # Converte objetos datetime para string
                entry["timestamp"] = entry["timestamp"]
                if "ultima_atualizacao" in entry["emotional_state"]:
                    entry["emotional_state"]["ultima_atualizacao"] = entry["emotional_state"]["ultima_atualizacao"].isoformat()
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        message_logs.clear()
        logger.info(f"📝 Logs salvos em {filename}")
    except Exception as e:
        logger.error(f"Erro ao salvar logs: {str(e)}")

def atualizar_historico(user_id: int, mensagem: str):
    """Mantém histórico conciso mas efetivo"""
    if user_id not in user_history:
        user_history[user_id] = []

    user_history[user_id].append(mensagem)

    # Mantém apenas as últimas mensagens
    if len(user_history[user_id]) > MAX_HISTORY:
        user_history[user_id] = user_history[user_id][-MAX_HISTORY:]

    return "\n".join(user_history[user_id])

async def stream_response(prompt: str, message: discord.Message):
    """Gera e envia resposta com streaming"""
    model = load_model()
    full_response = ""
    last_update = time.time()
    update_interval = 1.0  # Atualizar a cada 1 segundo
    response_message = None

    try:
        stream = model.create_completion(
            prompt,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            stop=["\n", "###", "<|im_end|>"],
            stream=True
        )

        for output in stream:
            token = output['choices'][0]['text']
            full_response += token

            # Envia/atualiza a mensagem periodicamente
            if time.time() - last_update > update_interval:
                if not response_message:
                    response_message = await message.reply(full_response + "▌")
                else:
                    await response_message.edit(content=full_response + "▌")
                last_update = time.time()

        # Envia a resposta final
        if response_message:
            await response_message.edit(content=full_response)
        else:
            await message.reply(full_response)

        return full_response

    except asyncio.TimeoutError:
        logger.warning("⏱️ Timeout na geração da resposta")
        return "Parece que preciso de mais tempo para pensar nisso..."

    except Exception as e:
        logger.error(f"🔴 Erro na geração: {str(e)}")
        return "Sinto muito, encontrei uma dificuldade técnica. Podemos tentar novamente?"

@bot.event
async def on_ready():
    logger.info(f"🤖 Conectada como {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.listening,
        name="mensagens e comandos"
    ))

@bot.command()
async def ajuda(ctx):
    """Mostra todos os comandos disponíveis"""
    embed = discord.Embed(
        title="💡 Comandos da Astéria",
        description="Comandos disponíveis para interagir comigo:",
        color=0x7289DA
    )
    embed.add_field(name="!reset", value="Reinicia nossa conversa", inline=False)
    embed.add_field(name="!estado", value="Mostra meu estado emocional atual", inline=False)
    embed.add_field(name="!info", value="Mostra informações detalhadas sobre mim", inline=False)
    embed.add_field(name="!logs", value="Mostra últimos logs (apenas criador)", inline=False)
    embed.set_footer(text="Respostas em tempo real com streaming")
    await ctx.send(embed=embed)

# ... (outros comandos mantidos como antes) ...

@bot.event
async def on_message(msg):
    start_time = time.time()

    # Ignora mensagens de outros bots
    if msg.author.bot:
        return

    logger.info(f"📩 {msg.author} ({msg.author.id}): {msg.content}")

    # Processar comandos primeiro
    await bot.process_commands(msg)

    # Verificar se deve responder
    responder = False
    if isinstance(msg.channel, discord.DMChannel):
        responder = True
    elif bot.user in msg.mentions:
        responder = True

    if not responder:
        return

    try:
        user_id = msg.author.id
        content = msg.clean_content.replace(f"<@{bot.user.id}>", "").strip()

        if not content:
            await msg.reply("👋 Sim, estou aqui! Como posso ajudar?")
            return

        # Detecção de idioma
        idioma = "pt"
        try:
            if len(content) > 10:
                idioma = detect(content)
                logger.info(f"🌐 Idioma detectado: {idioma}")
        except LangDetectException:
            pass

        instrucao = {
            "pt": "Você é Astéria. Responda em português de forma natural e concisa.",
            "en": "You are Astéria. Reply in natural, concise English."
        }.get(idioma[:2], "You are Astéria. Reply naturally in the user's language.")

        # Contexto emocional da persona
        contexto_emocional = asteria.construir_resposta(content)
        logger.info(f"💭 Contexto emocional: {contexto_emocional}")

        # Nota especial para o criador
        nota_criador = f"\nNota: Este usuário é meu criador, {msg.author.display_name}." if user_id == CRIADOR_ID else ""

        # Construção do prompt eficiente
        prompt_parts = [
            instrucao,
            nota_criador,
            f"Contexto emocional: {contexto_emocional}",
            atualizar_historico(user_id, f"Usuário: {content}"),
            "Astéria:"
        ]
        prompt = "\n".join(filter(None, prompt_parts))

        # Geração e envio da resposta com streaming
        async with msg.channel.typing():
            resposta = await stream_response(prompt, msg)
            elapsed = time.time() - start_time

            # Log detalhado
            log_message(user_id, str(msg.author), content, resposta, elapsed)
            logger.info(f"⏱️ TEMPO TOTAL: {elapsed:.2f}s | Resposta: {resposta[:80]}{'...' if len(resposta) > 80 else ''}")

            # Atualizar histórico
            atualizar_historico(user_id, f"Astéria: {resposta}")

    except Exception as e:
        logger.exception(f"🔴 ERRO NO MESSAGE: {str(e)}")
        await msg.reply("❌ Ocorreu um erro inesperado. Por favor, tente novamente.")

# Salvar logs ao sair
@bot.event
async def on_disconnect():
    save_logs_to_file()
    logger.info("🔌 Desconectado. Logs salvos.")

if __name__ == "__main__":
    try:
        load_model()  # Pré-carrega o modelo
        bot.run(TOKEN)
    finally:
        save_logs_to_file()  # Garante salvamento final
