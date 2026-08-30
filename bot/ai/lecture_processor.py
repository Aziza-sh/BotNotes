from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

import pymupdf4llm
from docx import Document

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import (
    JsonOutputParser,
    StrOutputParser,
)
from langchain_ollama import ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ============================================================
# Logging
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================
# Config
# ============================================================


@dataclass(slots=True, frozen=True)
class AIConfig:

    model: str = "qwen2.5:7b"

    summary_temperature: float = 0.05

    qa_temperature: float = 0.1

    # Контекст уменьшен и УНИФИЦИРОВАН для summary и qa,
    # чтобы Ollama не перезагружала модель при переключении
    # между функциями (это дорого на слабом железе).
    summary_ctx: int = 4096

    qa_ctx: int = 4096

    # Чанки меньше -> меньше памяти и меньше токенов
    # генерируется за один запрос.
    chunk_size: int = 3000

    chunk_overlap: int = 300

    cache_suffix: str = ".summary.md"

    questions_suffix: str = ".questions.md"

    questions_count: int = 5

    # Сколько раз повторить запрос при 503 / ошибке связи
    max_retries: int = 4

    # Базовая задержка перед повтором (сек), растёт экспоненциально
    retry_base_delay: float = 5.0

    # Пауза между чанками, чтобы дать модели/системе передохнуть
    pause_between_chunks: float = 2.0

    # Модель остаётся в памяти между запросами (не выгружается
    # и не грузится заново каждый раз)
    keep_alive: str = "30m"


CONFIG = AIConfig()


# ============================================================
# LLM
# ============================================================

SUMMARY_LLM = ChatOllama(
    model=CONFIG.model,
    temperature=CONFIG.summary_temperature,
    num_ctx=CONFIG.summary_ctx,
    keep_alive=CONFIG.keep_alive,
)

QA_LLM = ChatOllama(
    model=CONFIG.model,
    temperature=CONFIG.qa_temperature,
    num_ctx=CONFIG.qa_ctx,
    format="json",
    keep_alive=CONFIG.keep_alive,
)


# ============================================================
# Retry helper
# ============================================================


def invoke_with_retry(chain, payload: dict, label: str = "request"):
    """
    Вызывает chain.invoke с повторными попытками.

    Полезно, когда Ollama временно отвечает 503
    (перегружена / модель ещё грузится / не хватает ресурсов).
    """

    last_error: Exception | None = None

    for attempt in range(1, CONFIG.max_retries + 1):

        try:
            return chain.invoke(payload)

        except Exception as exc:

            last_error = exc

            delay = CONFIG.retry_base_delay * attempt

            logger.warning(
                "%s: попытка %s/%s не удалась (%s). Повтор через %.1f сек...",
                label,
                attempt,
                CONFIG.max_retries,
                exc,
                delay,
            )

            time.sleep(delay)

    logger.error(
        "%s: все %s попыток исчерпаны.",
        label,
        CONFIG.max_retries,
    )

    raise last_error


# ============================================================
# Prompts
# ============================================================

MAP_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
Ты — преподаватель университета.

Тебе дают ОДНУ часть большой лекции.

Создай максимально качественный
академический конспект.

Правила

• Не теряй определения.

• Не теряй формулы.

• Не теряй доказательства.

• Не теряй примеры.

• Не теряй важные замечания.

• Удали воду.

• Сделай структуру красивой.

Используй Markdown.

Используй:

# Заголовки

## Подзаголовки

### Списки

Формулы оформляй через LaTeX.

Не используй фразы

"в этой части"

"автор рассказывает"

"далее говорится"

Отвечай только на русском языке.
""",
        ),
        (
            "human",
            """
Текст:

{text}
""",
        ),
    ]
)

REDUCE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
Ты получил несколько конспектов одной лекции.

Объедини их.

Удаляй повторы.

Объединяй одинаковые определения.

Выстраивай материал логически.

Если определения встречаются несколько раз —
оставь лучшее.

Сохрани абсолютно всю важную информацию.

Не сокращай материал без необходимости.

Верни единый красивый Markdown.
""",
        ),
        (
            "human",
            """
Конспекты:

{text}
""",
        ),
    ]
)

QA_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            f"""
Ты преподаватель.

Сгенерируй ровно
{CONFIG.questions_count}
контрольных вопросов.

Ответ только JSON.

{{
    "questions":[
        "...",
        "...",
        "...",
        "...",
        "..."
    ]
}}
""",
        ),
        (
            "human",
            """
Материал:

{text}
""",
        ),
    ]
)


# ============================================================
# Chains
# ============================================================

map_chain = MAP_PROMPT | SUMMARY_LLM | StrOutputParser()

reduce_chain = REDUCE_PROMPT | SUMMARY_LLM | StrOutputParser()

qa_chain = QA_PROMPT | QA_LLM | JsonOutputParser()


# ============================================================
# Text extraction
# ============================================================


def extract_text(path: str | Path) -> str:

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(path)

    logger.info("Reading %s", path.name)

    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return pymupdf4llm.to_markdown(str(path))

    if suffix == ".docx":

        document = Document(path)

        paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]

        return "\n\n".join(paragraphs)

    raise ValueError(f"{suffix} is not supported.")


# ============================================================
# Splitter
# ============================================================

splitter = RecursiveCharacterTextSplitter(
    chunk_size=CONFIG.chunk_size,
    chunk_overlap=CONFIG.chunk_overlap,
    separators=[
        "\n\n",
        "\n",
        ". ",
        " ",
        "",
    ],
)


def split_text(text: str) -> list[str]:

    chunks = splitter.split_text(text)

    logger.info(
        "Document split into %s chunks.",
        len(chunks),
    )

    return chunks


# ============================================================
# Summary generation
# ============================================================


def generate_summary(markdown: str) -> str:
    """
    Генерирует единый конспект документа
    по схеме Map -> Reduce.
    """

    chunks = split_text(markdown)

    logger.info("Starting MAP stage...")

    partial_summaries: list[str] = []

    total = len(chunks)

    for index, chunk in enumerate(chunks, start=1):

        logger.info(
            "Chunk %s/%s",
            index,
            total,
        )

        try:

            result = invoke_with_retry(
                map_chain,
                {"text": chunk},
                label=f"MAP chunk {index}/{total}",
            )

            partial_summaries.append(result)

        except Exception:

            logger.exception(
                "Chunk %s failed after retries.",
                index,
            )

        # небольшая пауза между чанками, чтобы не душить слабое железо
        if index < total:
            time.sleep(CONFIG.pause_between_chunks)

    logger.info("MAP stage finished.")

    if not partial_summaries:
        raise RuntimeError(
            "Не удалось получить ни одного конспекта чанка. "
            "Проверь, что Ollama запущена и модель доступна."
        )

    logger.info("Starting REDUCE stage...")

    merged = "\n\n---\n\n".join(partial_summaries)

    final_summary = invoke_with_retry(
        reduce_chain,
        {"text": merged},
        label="REDUCE stage",
    )

    logger.info("Summary generated successfully.")

    return final_summary


# ============================================================
# Questions generation
# ============================================================


def generate_questions(summary: str) -> list[str]:

    logger.info("Generating questions...")

    try:

        response = invoke_with_retry(
            qa_chain,
            {"text": summary},
            label="QA generation",
        )

        questions = response.get("questions", [])

        if not isinstance(questions, list):
            return []

        logger.info(
            "%s questions generated.",
            len(questions),
        )

        return questions

    except Exception:

        logger.exception("Questions generation failed after retries.")

        return []


# ============================================================
# Cache
# ============================================================


def summary_cache(path: Path) -> Path:
    return Path(str(path) + CONFIG.cache_suffix)


def questions_cache(path: Path) -> Path:
    return Path(str(path) + CONFIG.questions_suffix)


# ============================================================
# Public API
# ============================================================


def summarize_file(
    file_path: str | Path,
    use_cache: bool = True,
) -> str:
    """
    Получить конспект документа.

    При наличии
    *.summary.md
    используется кэш.
    """

    path = Path(file_path)

    cache = summary_cache(path)

    if use_cache and cache.exists():

        logger.info("Using cached summary.")

        return cache.read_text(
            encoding="utf-8",
        )

    logger.info("Extracting text...")

    markdown = extract_text(path)

    logger.info("Generating summary...")

    summary = generate_summary(markdown)

    cache.write_text(
        summary,
        encoding="utf-8",
    )

    logger.info(
        "Summary saved to %s",
        cache.name,
    )

    return summary


def get_questions(
    file_path: str | Path,
    use_cache: bool = True,
) -> list[str]:
    """
    Получить вопросы по документу.

    Если существует
    *.questions.md

    повторная генерация
    не выполняется.
    """

    path = Path(file_path)

    cache = questions_cache(path)

    if use_cache and cache.exists():

        logger.info("Using cached questions.")

        questions = []

        for line in cache.read_text(
            encoding="utf-8",
        ).splitlines():

            line = line.strip()

            if line.startswith("- "):
                questions.append(line[2:])

        return questions

    summary = summarize_file(
        path,
        use_cache=use_cache,
    )

    questions = generate_questions(summary)

    markdown = "\n".join(f"- {question}" for question in questions)

    cache.write_text(
        markdown,
        encoding="utf-8",
    )

    logger.info(
        "Questions saved to %s",
        cache.name,
    )

    return questions


def process_document(
    file_path: str | Path,
):
    """
    Полная обработка документа.

    Returns
    -------

    tuple[
        summary,
        questions
    ]
    """

    summary = summarize_file(file_path)

    questions = get_questions(file_path)

    return summary, questions


# ============================================================
# Local запуск
# ============================================================

if __name__ == "__main__":

    file = Path("lecture.pdf")

    if not file.exists():

        logger.error(
            "File %s not found.",
            file,
        )

        raise SystemExit(1)

    summary, questions = process_document(file)

    print()

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print(summary)

    print()

    print("=" * 80)
    print("QUESTIONS")
    print("=" * 80)

    for i, question in enumerate(
        questions,
        start=1,
    ):
        print(f"{i}. {question}")
