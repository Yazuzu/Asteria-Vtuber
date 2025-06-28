#!/bin/bash

echo "🔧 Iniciando configuração do projeto Astéria..."

PROJECT_DIR="$HOME/bot"
MODEL_DIR="$HOME/models"
MODEL_NAME="nous-hermes-2-mistral-7b.Q4_K_M.gguf"
MODEL_URL="https://huggingface.co/TheBloke/Nous-Hermes-2-Mistral-7B-GGUF/resolve/main/$MODEL_NAME"

# 1. Criar estrutura de arquivos Python
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

echo "📁 Criando arquivos Python..."
cat > modelo.py <<EOF
from gpt4all import GPT4All

def carregar_modelo():
    return GPT4All("$MODEL_NAME", model_path="$MODEL_DIR", allow_download=False)
EOF

cat > persona.py <<EOF
class Asteria:
    def __init__(self):
        self.nome = "Astéria"
        self.descricao = (
            "Uma jovem com mentalidade forte, extrovertida, provocadora, "
            "com estilo refinado e fã de lógica e debates."
        )

    def responder(self, texto_usuario, emocao="neutro"):
        base = f"Você disse: '{texto_usuario}'."
        if emocao == "raiva":
            return f"{base} Ugh... que perda de tempo."
        elif emocao == "alegria":
            return f"{base} Isso me anima! Fofo você."
        elif emocao == "tristeza":
            return f"{base} Espero que fique bem logo..."
        elif emocao == "sarcasmo":
            return f"{base} Claro, porque isso faz TODO sentido..."
        return f"{base} Entendi."
EOF

cat > historico.py <<EOF
MAX_HISTORY = 20
history = {}

def atualizar_historico(user_id, nova_msg):
    msgs = history.get(user_id, [])
    msgs.append(nova_msg)
    history[user_id] = msgs[-MAX_HISTORY:]
    return "\\n".join(history[user_id])
EOF

cat > bot.py <<EOF
import discord
from discord.ext import commands
import asyncio
from modelo import carregar_modelo
from persona import Asteria
from historico import atualizar_historico

model = carregar_modelo()
print("✅ Modelo carregado!")

TOKEN = "COLE_SEU_TOKEN_AQUI"
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
asteria = Asteria()

async def gerar_resposta(prompt):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, model.generate, prompt)

@bot.event
async def on_ready():
    print(f"🤖 Astéria conectada como {bot.user}!")

@bot.event
async def on_message(msg):
    if msg.author == bot.user: return
    if isinstance(msg.channel, discord.DMChannel):
        contexto = atualizar_historico(msg.author.id, msg.content)
        resposta = await gerar_resposta(contexto)
        atualizar_historico(msg.author.id, resposta)
        await msg.channel.send(resposta)
    await bot.process_commands(msg)

if __name__ == "__main__":
    bot.run(TOKEN)
EOF

# 2. Baixar modelo Hermes
mkdir -p "$MODEL_DIR"
echo "⬇️ Baixando modelo Hermes..."
wget -q --show-progress -O "$MODEL_DIR/$MODEL_NAME" "$MODEL_URL"

# 3. Limpar modelos antigos
echo "🧹 Removendo modelos antigos..."
find "$MODEL_DIR" -type f ! -name "$MODEL_NAME" -delete

echo "✅ Tudo pronto! Edite bot.py e adicione seu token."
