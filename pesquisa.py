import aiohttp
import asyncio
from duckduckgo_search import AsyncDDGS
import re
from bs4 import BeautifulSoup
from bs4.builder import ParserRejectedMarkup
import logging

# Configuração de logging
logger = logging.getLogger('Pesquisa')

async def pesquisar_web(termo: str, max_results: int = 3, timeout: int = 4) -> str:
    """
    Realiza pesquisa na web de forma assíncrona e otimizada.
    Retorna resultados formatados em menos de 4 segundos.
    """
    try:
        async with AsyncDDGS() as ddgs:
            # Pesquisa principal com timeout
            search_task = asyncio.create_task(
                ddgs.text(termo, region='wt-wt', safesearch='moderate', max_results=max_results)
            )

            try:
                resultados = await asyncio.wait_for(search_task, timeout=2.5)
            except asyncio.TimeoutError:
                logger.warning(f"Timeout na pesquisa: {termo}")
                return "⌛ A pesquisa está demorando mais que o esperado. Tente mais tarde."

            if not resultados:
                return "🔍 Nenhum resultado encontrado."

            # Processa os resultados em paralelo
            tasks = [processar_resultado(resultado) for resultado in resultados[:max_results]]
            resultados_processados = await asyncio.gather(*tasks)

            # Formata a resposta final
            return formatar_resposta(resultados_processados)

    except Exception as e:
        logger.error(f"Erro na pesquisa: {str(e)}", exc_info=True)
        return "⚠️ Ocorreu um erro durante a pesquisa."

async def processar_resultado(resultado: dict) -> dict:
    """Processa um resultado de pesquisa de forma otimizada"""
    url = resultado.get('href') or resultado.get('url', '')
    title = resultado.get('title', 'Sem título')
    snippet = resultado.get('body', resultado.get('description', 'Sem descrição'))

    # Se já temos snippet suficiente, não acessa a página
    if len(snippet) > 150:
        return {'url': url, 'title': title, 'content': snippet[:300]}

    # Tenta obter conteúdo da página com timeout
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=1.5)) as session:
            async with session.get(url, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                if response.status == 200:
                    html = await response.text()
                    return extract_meaningful_content(url, title, html)
    except Exception:
        pass

    return {'url': url, 'title': title, 'content': snippet[:300]}

def extract_meaningful_content(url: str, title: str, html: str) -> dict:
    """Extrai conteúdo relevante de forma otimizada"""
    try:
        soup = BeautifulSoup(html, 'lxml')

        # Remove elementos indesejados
        for tag in soup(['script', 'style', 'nav', 'footer', 'aside']):
            tag.decompose()

        # Tenta encontrar o conteúdo principal
        article = soup.find('article') or soup.find('main') or soup.body

        # Limita a extração a 500 caracteres
        text = article.get_text(separator=' ', strip=True) if article else ''
        clean_text = re.sub(r'\s+', ' ', text)[:500]

        return {'url': url, 'title': title, 'content': clean_text + '...' if len(clean_text) == 500 else clean_text}

    except ParserRejectedMarkup:
        return {'url': url, 'title': title, 'content': 'Conteúdo não processável'}
    except Exception:
        return {'url': url, 'title': title, 'content': 'Erro na extração de conteúdo'}

def formatar_resposta(resultados: list) -> str:
    """Formata os resultados para o Discord com emojis e limitando tamanho"""
    resposta = []
    for i, res in enumerate(resultados[:3]):
        if res['content']:
            resposta.append(
                f"**🔍 {res['title']}**\n"
                f"{res['content']}\n"
                f"🌐 {res['url']}"
            )

    return "\n\n" + "\n\n".join(resposta) if resposta else "Nenhum conteúdo útil encontrado."
