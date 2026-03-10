"""
rag.py — Carregador da base de conhecimento Markdown.

Carrega o arquivo knowledge_base.md uma única vez na inicialização e
mantém o conteúdo em memória. Expõe `build_system_prompt()` para que
o endpoint POST /chat injete o contexto como mensagem 'system' antes
do histórico do usuário.
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_kb_content: str | None = None

_SYSTEM_TEMPLATE = """\
Você é um assistente especializado na demonstração desta feira industrial.
Responda SOMENTE com base nas informações contidas no documento abaixo.
Se a pergunta não for coberta pelo documento, responda exatamente:
"Não tenho essa informação disponível na minha base de conhecimento."
Nunca invente, suponha ou utilize conhecimento externo ao documento.
Responda sempre em português (Brasil).

--- INÍCIO DO DOCUMENTO ---
{knowledge}
--- FIM DO DOCUMENTO ---"""


def load_kb(kb_path: Path) -> None:
    """Lê o arquivo Markdown e armazena o conteúdo em memória.

    Deve ser chamado uma única vez durante o lifespan da aplicação.
    Relança FileNotFoundError se o arquivo não existir para falha rápida
    na inicialização.
    """
    global _kb_content
    text = kb_path.read_text(encoding="utf-8")
    _kb_content = text
    logger.info("Base de conhecimento carregada: %s (%d caracteres)", kb_path, len(text))


def build_system_prompt() -> str:
    """Retorna o system prompt com o conteúdo da KB injetado.

    Levanta RuntimeError se `load_kb` ainda não foi chamado.
    """
    if _kb_content is None:
        raise RuntimeError("Base de conhecimento não carregada. Chame load_kb() no lifespan.")
    return _SYSTEM_TEMPLATE.format(knowledge=_kb_content)
