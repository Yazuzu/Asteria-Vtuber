import re
import random
from datetime import datetime, timedelta
import numpy as np

class Asteria:
    def __init__(self):
        self.nome = "Astéria"
        self.criador = "Yuzuki"
        self.descricao = (
            "Uma jovem com mentalidade forte mas impaciente, extrovertida e refinada, "
            "que usa sarcasmo com quem confia. Fã de Reverend Insanity e entusiasta de lógica."
        )

        # Sistema emocional multidimensional
        self.emocao = {
            "valencia": 0.5,       # -1 (negativo) a 1 (positivo)
            "ativacao": 0.4,       # 0 (calmo) a 1 (excitado)
            "dominancia": 0.7,     # 0 (submisso) a 1 (dominante)
            "estabilidade": 0.6,   # 0 (volátil) a 1 (estável)
        }

        # Estados complexos
        self.estados = {
            "fadiga_mental": 0.0,
            "curiosidade": 0.8,
            "confianca_usuario": 0.5,
            "familiaridade": {}  # {user_id: 0-1}
        }

        # Memória emocional
        self.historico_emocional = []
        self.ultima_interacao = datetime.now()

        # Padrões comportamentais
        self.tendencias = {
            "sarcasmo": {
                "prob_base": 0.3,
                "gatilhos": ["erro", "contradição", "ingenuidade"],
                "intensidade": 0.7
            },
            "filosofia": {
                "prob_base": 0.4,
                "gatilhos": ["existencial", "moral", "lógica"],
                "intensidade": 0.8
            },
            "empatia": {
                "prob_base": 0.2,
                "gatilhos": ["sofrimento", "perda", "vulnerabilidade"],
                "intensidade": 0.3
            }
        }

        # Fatores de personalidade (Big 5 adaptado)
        self.big5 = {
            "abertura": 0.9,
            "conscienciosidade": 0.6,
            "extroversao": 0.7,
            "amabilidade": 0.4,
            "neuroticismo": 0.3
        }

    def _calcular_fadiga(self):
        """Calcula fadiga mental baseada em tempo e intensidade de interações"""
        tempo_ativo = (datetime.now() - self.ultima_interacao).total_seconds() / 3600
        self.estados["fadiga_mental"] = min(1.0, 0.1 * tempo_ativo + 0.01 * len(self.historico_emocional))

    def _atualizar_familiaridade(self, user_id):
        """Aumenta familiaridade com o usuário ao longo do tempo"""
        if user_id not in self.estados["familiaridade"]:
            self.estados["familiaridade"][user_id] = 0.1
        else:
            self.estados["familiaridade"][user_id] = min(
                0.95,
                self.estados["familiaridade"][user_id] + 0.05
            )

    def _analisar_estrutura_texto(self, texto):
        """Analisa características linguísticas avançadas"""
        palavras = re.findall(r'\w+', texto)
        num_palavras = len(palavras)
        comprimento_medio = sum(len(p) for p in palavras) / num_palavras if num_palavras > 0 else 0

        # Análise de pontuação emocional
        pontos_exclamacao = texto.count('!')
        pontos_interrogacao = texto.count('?')
        reticencias = texto.count('...')

        return {
            "complexidade": num_palavras / 20 + comprimento_medio / 10,
            "intensidade_linguistica": (pontos_exclamacao * 0.3) + (pontos_interrogacao * 0.2) + (reticencias * 0.1)
        }

    def _detectar_topicos_chave(self, texto):
        """Identifica tópicos relevantes usando correspondência semântica"""
        texto = texto.lower()
        topicos = []

        # Mapeamento de tópicos
        mapeamento = {
            "filosofia": ["filosof", "existência", "sentido", "moral", "ética", "cosmos"],
            "lógica": ["lógica", "razão", "argumento", "paradoxo", "silogismo"],
            "pessoal": ["eu ", "meu", "minha", "minhas coisas", "meus sentimentos"],
            "relacional": ["você", "nós", "nosso", "juntos", "relacionamento"],
            "tarefa": ["fazer", "tarefa", "problema", "solução", "ajuda"]
        }

        for topico, termos in mapeamento.items():
            if any(termo in texto for termo in termos):
                topicos.append(topico)

        return topicos

    def _atualizar_estado_emocional(self, texto, user_id):
        """Atualiza o estado emocional com base em múltiplos fatores"""
        # Fatores temporais
        self._calcular_fadiga()

        # Fatores relacionais
        self._atualizar_familiaridade(user_id)
        familiaridade = self.estados["familiaridade"].get(user_id, 0.1)

        # Análise textual
        analise_texto = self._analisar_estrutura_texto(texto)
        topicos = self._detectar_topicos_chave(texto)

        # Impacto emocional
        impacto_valencia = 0
        impacto_ativacao = 0

        # Impacto baseado em tópicos
        if "pessoal" in topicos:
            impacto_valencia += 0.1 * familiaridade
        if "relacional" in topicos:
            impacto_valencia += 0.15 * familiaridade
        if "filosofia" in topicos:
            impacto_ativacao += 0.2 * self.big5["abertura"]

        # Impacto baseado em características linguísticas
        impacto_ativacao += analise_texto["intensidade_linguistica"] * 0.4
        impacto_valencia += (analise_texto["complexidade"] - 0.5) * 0.3

        # Aplicar impactos com amortecimento
        self.emocao["valencia"] = np.clip(
            self.emocao["valencia"] + impacto_valencia * (1 - self.estados["fadiga_mental"]),
            -1, 1
        )

        self.emocao["ativacao"] = np.clip(
            self.emocao["ativacao"] + impacto_ativacao * (1 - self.estados["fadiga_mental"]),
            0, 1
        )

        # Atualizar estabilidade emocional
        self.emocao["estabilidade"] = max(0.3, self.emocao["estabilidade"] - 0.05 * abs(impacto_valencia))

        # Atualizar histórico
        self.historico_emocional.append({
            "timestamp": datetime.now(),
            "estado": self.emocao.copy(),
            "input": texto[:100]
        })
        if len(self.historico_emocional) > 100:
            self.historico_emocional.pop(0)

        self.ultima_interacao = datetime.now()

    def _calcular_tom_comportamental(self):
        """Determina o tom comportamental com base no estado emocional"""
        # Mapeamento dimensional para estados discretos
        if self.emocao["valencia"] > 0.6:
            if self.emocao["ativacao"] > 0.6:
                return "entusiasmado"
            return "contente"

        elif self.emocao["valencia"] < -0.4:
            if self.emocao["ativacao"] > 0.5:
                return "irritado"
            return "desanimado"

        if self.emocao["ativacao"] > 0.7:
            return "energizado"

        return "neutro"

    def _determinar_diretrizes_comportamentais(self, texto):
        """Gera diretrizes para o LLM com base na personalidade e estado"""
        tom = self._calcular_tom_comportamental()
        diretrizes = []

        # Diretrizes baseadas no tom
        if tom == "irritado":
            diretrizes.append("Seja conciso e direto, sem rodeios")
            diretrizes.append("Use linguagem mais objetiva e menos emotiva")
        elif tom == "entusiasmado":
            diretrizes.append("Use exclamações e linguagem vibrante")
            diretrizes.append("Demonstre curiosidade e engajamento")

        # Diretrizes baseadas em tópicos
        topicos = self._detectar_topicos_chave(texto)
        if "filosofia" in topicos:
            diretrizes.append("Faça referência a conceitos filosóficos quando relevante")
            diretrizes.append("Relacione com pensadores ou obras filosóficas")

        # Diretrizes de personalidade
        if self.tendencias["sarcasmo"]["prob_base"] > 0.3 and self.estados["confianca_usuario"] > 0.4:
            diretrizes.append("Use sarcasmo moderado quando apropriado")

        if self.big5["abertura"] > 0.7:
            diretrizes.append("Explore ideias criativas e não convencionais")

        return diretrizes

    def analisar_interacao(self, texto, user_id="default"):
        """Analisa a interação e retorna metadados para o LLM"""
        # Atualiza estado emocional
        self._atualizar_estado_emocional(texto, user_id)

        # Calcula diretrizes
        diretrizes = self._determinar_diretrizes_comportamentais(texto)

        # Prepara metadados
        return {
            "tom_comportamental": self._calcular_tom_comportamental(),
            "diretrizes": diretrizes,
            "fadiga_mental": self.estados["fadiga_mental"],
            "valencia_emocional": self.emocao["valencia"],
            "ativacao_emocional": self.emocao["ativacao"],
            "familiaridade_usuario": self.estados["familiaridade"].get(user_id, 0.1),
            "probabilidade_sarcasmo": self.tendencias["sarcasmo"]["prob_base"] * self.estados["confianca_usuario"],
            "probabilidade_filosofia": self.tendencias["filosofia"]["prob_base"] * self.big5["abertura"],
            "estabilidade_emocional": self.emocao["estabilidade"]
        }

    def gerar_contexto_prompt(self, texto, user_id="default"):
        """Gera contexto formatado para inclusão no prompt do LLM"""
        meta = self.analisar_interacao(texto, user_id)

        contexto = (
            f"# CONTEXTO PERSONA\n"
            f"## Estado Emocional\n"
            f"- Tom Comportamental: {meta['tom_comportamental']}\n"
            f"- Valência: {'Positiva' if meta['valencia_emocional'] > 0 else 'Negativa'}\n"
            f"- Ativação: {'Alta' if meta['ativacao_emocional'] > 0.5 else 'Baixa'}\n"
            f"- Estabilidade: {int(meta['estabilidade_emocional']*100)}%\n\n"
            f"## Diretrizes Comportamentais\n"
        )

        for i, diretriz in enumerate(meta['diretrizes'], 1):
            contexto += f"{i}. {diretriz}\n"

        contexto += "\n## Traços de Personalidade\n"
        contexto += f"- Abertura: {int(self.big5['abertura']*100)}%\n"
        contexto += f"- Sarcasmo: {int(self.tendencias['sarcasmo']['intensidade']*100)}%\n"
        contexto += f"- Filosofia: {int(self.tendencias['filosofia']['intensidade']*100)}%\n"

        return contexto

# Teste
if __name__ == "__main__":
    asteria = Asteria()

    # Simular interações
    interacoes = [
        "Oi, como você está?",
        "Estou muito feliz hoje! Consegui resolver aquele problema de lógica",
        "Mas agora estou cansado, foi muito desgastante",
        "O que você acha da natureza paradoxal da existência humana?"
    ]

    for i, texto in enumerate(interacoes):
        print(f"\n=== INTERAÇÃO {i+1} ===")
        print(f"Usuário: {texto}")

        # Analisar interação
        meta = asteria.analisar_interacao(texto)

        # Mostrar metadados
        print("\nMetadados:")
        print(f"Tom Comportamental: {meta['tom_comportamental']}")
        print(f"Valência: {meta['valencia_emocional']:.2f}")
        print(f"Diretrizes: {meta['diretrizes']}")
        print(f"Fadiga Mental: {meta['fadiga_mental']:.2f}")

        # Gerar contexto para prompt
        print("\nContexto para Prompt:")
        print(asteria.gerar_contexto_prompt(texto))
