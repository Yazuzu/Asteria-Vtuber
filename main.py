import datetime
import time
import os
import json
import re
import sys
from modelo import carregar_modelo
from persona import Asteria

class ConversationManager:
    def __init__(self):
        self.model = carregar_modelo()
        self.persona = Asteria()
        self.history = []
        self.log_dir = "logs"
        os.makedirs(self.log_dir, exist_ok=True)
        self.user_id = "default"
        self.streaming_delay = 0.02  # Delay entre tokens para efeito de streaming

        # Configurações otimizadas
        self.settings = {
            "max_history": 2,
            "max_tokens": 80,
            "temperature": 0.7,
            "cache_size": 10
        }
        self.prompt_cache = {}

        print(f"\n🧠 {self.persona.nome} iniciada - Personalidade: {self.persona.descricao[:60]}...")
        print("Digite 'sair' ou '/ajuda' para comandos\n")

    def generate_response(self, user_input: str) -> (str, float):
        """Gera resposta com streaming visual"""
        persona_context = self.persona.gerar_contexto_prompt(user_input, self.user_id)
        prompt = self._build_minimal_prompt(user_input, persona_context)

        start = time.time()
        full_response = ""
        displayed_response = ""

        try:
            # Geração com streaming
            stream = self.model.create_completion(
                prompt,
                max_tokens=self.settings["max_tokens"],
                temperature=self.settings["temperature"],
                stop=["\n", "###"],
                stream=True
            )

            # Imprime o prefixo antes de começar
            now = datetime.datetime.now()
            timestamp_str = now.strftime("[%H:%M:%S]")
            sys.stdout.write(f"{timestamp_str} {self.persona.nome}: ")
            sys.stdout.flush()

            # Processa cada token do stream
            for output in stream:
                token = output['choices'][0]['text']
                full_response += token

                # Exibe o token com efeito de streaming
                sys.stdout.write(token)
                sys.stdout.flush()
                time.sleep(self.streaming_delay)

            # Limpeza da resposta
            full_response = re.sub(r'[<>\[\]]', '', full_response).strip()
            print()  # Nova linha após conclusão

        except Exception as e:
            full_response = f"Erro: {str(e)}"
            print(f"{timestamp_str} {self.persona.nome}: {full_response}")

        elapsed = time.time() - start
        self._update_history(user_input, full_response, elapsed)
        return full_response, elapsed

    def _build_minimal_prompt(self, user_input: str, persona_context: str) -> str:
        """Prompt mínimo para streaming eficiente"""
        # Histórico compactado
        history_segment = ""
        for i, (q, a) in enumerate(self.history[-self.settings["max_history"]:]):
            history_segment += f"\nU{i+1}: {q[:20]}"[:20]
            if a:  # Evita linha vazia se não houver resposta
                history_segment += f"\nA{i+1}: {a[:20]}"[:20]

        # Prompt essencial
        return (
            f"Contexto: {persona_context[:100]}\n"
            f"Histórico:{history_segment}"
            f"\nU: {user_input}\nA:"
        )

    def _update_history(self, user_input: str, response: str, response_time: float):
        self.history.append((user_input, response))
        if len(self.history) > 5:
            self.history.pop(0)

    def save_log(self, user_input: str, response: str, timestamp: datetime.datetime):
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "user_input": user_input,
            "response": response,
        }

        filename = os.path.join(self.log_dir, f"conversa_{datetime.date.today().isoformat()}.jsonl")
        with open(filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    def interactive_loop(self):
        while True:
            try:
                now = datetime.datetime.now()
                timestamp_str = now.strftime("[%H:%M:%S]")

                user_input = input(f"{timestamp_str} Você: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ("sair", "exit", "quit"):
                    print("\nAté logo!")
                    break

                if user_input.startswith('/'):
                    self.handle_command(user_input)
                    continue

                start_time = time.time()
                response, elapsed = self.generate_response(user_input)

                # Mostrar métricas apenas se demorar
                if elapsed > 0.5:
                    print(f"⏱ {elapsed:.2f}s | 💬 {len(response.split())} tokens")

                self.save_log(user_input, response, now)

            except KeyboardInterrupt:
                print("\n\nEncerrando...")
                break
            except Exception as e:
                print(f"⚠️ Erro: {str(e)}")

    def handle_command(self, command: str):
        cmd = command.lower()

        if cmd == '/ajuda':
            print("\nComandos:")
            print("/estado - Mostrar estado emocional")
            print("/limpar - Limpar histórico da sessão")
            print("/sair - Encerrar conversa")

        elif cmd == '/estado':
            print(f"\n💖 Estado emocional atual:")
            print(f"Tom: {getattr(self.persona, 'tom_comportamental', 'neutro')}")
            print(f"Valência: {getattr(self.persona, 'valencia_emocional', 0.5):.1f}")

        elif cmd == '/limpar':
            self.history = []
            self.prompt_cache = {}
            print("\n🆑 Histórico limpo!")

        else:
            print(f"\nComando desconhecido: {command}")

def main():
    ConversationManager().interactive_loop()

if __name__ == "__main__":
    main()
