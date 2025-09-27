from typing import Literal, override, Any

from gpt_researcher.config.variables.base import BaseConfig
from gpt_researcher.config.config import Config
from gpt_researcher import GPTResearcher
from gpt_researcher.actions.retriever import get_retrievers
from gpt_researcher.prompts import get_prompt_family
from gpt_researcher.memory.embeddings import Memory

from gpt_researcher.config import Config
from gpt_researcher.memory import Memory
from gpt_researcher.utils.enum import ReportSource, ReportType, Tone
from gpt_researcher.prompts import get_prompt_family
from gpt_researcher.vector_store import VectorStoreWrapper
from gpt_researcher.skills.researcher import ResearchConductor
from gpt_researcher.skills.writer import ReportGenerator
from gpt_researcher.skills.context_manager import ContextManager
from gpt_researcher.skills.browser import BrowserManager
from gpt_researcher.skills.curator import SourceCurator
from gpt_researcher.skills.deep_research import DeepResearchSkill

from gpt_researcher.actions import (
    get_retrievers,
)

LLM_DEFAULTS = {
    "gpt-5": {
        "fast": "gpt-5-mini",
        "smart": "gpt-5",
    },
    "gpt-4.1": {
        "fast": "gpt-4.1-mini",
        "smart": "gpt-4.1",
    },
    "mistral-large-2407": {
        "fast": "mistral-large-2407",
          "smart": "mistral-large-2407"
    },
    "anthropic": {
        "fast": "claude-3-5-haiku",
        "smart": "claude-3-5-sonnet",
    },
    "gemini-2.5": {
        "fast": "gemini-2.5-flash",
        "smart": "gemini-2.5-pro",
    },
}

type Provider = Literal[
    "openai",
    "mistralai",
    "google_genai",
    "anthropic",
]

PROVIDER_2_EMBEDDING: dict[Provider, str] = {
    "openai": "openai:text-embedding-3-small",
    "mistralai": "mistralai:mistral-embed",
    "google_genai": "google_genai:models/text-embedding-004",
    "anthropic": "anthropic:claude-3-embedding",
}

PROVIDER_2_STRATEGIC: dict[Provider, str] = {
    "openai": "openai:gpt-o4-mini",
    "mistralai": "mistralai:mistral-large-2407",
    "google_genai": "google_genai:gemini-2.5-pro",
    "anthropic": "anthropic:claude-3",
}


def _create_config(
    provider: Provider,
    model: str,
    similarity_threshold: float = 0.42,
    fast_token_limit: int = 3000,
    smart_token_limit: int = 6000,
    strategic_token_limit: int = 4000,
    temperature: float = 0.4,
    total_words: int = 1200,
    max_iterations: int = 3,
) -> BaseConfig:
    fast_llm = f"{provider}:{LLM_DEFAULTS[model]['fast']}"
    smart_llm = f"{provider}:{LLM_DEFAULTS[model]['smart']}"

    return {
        "RETRIEVER": "tavily",
        "EMBEDDING": PROVIDER_2_EMBEDDING[provider],
        "SIMILARITY_THRESHOLD": similarity_threshold,
        "FAST_LLM": fast_llm,
        "SMART_LLM": smart_llm,  # Has support for long responses (2k+ words).
        "STRATEGIC_LLM": PROVIDER_2_STRATEGIC[
            provider
        ],  # Can be used with o1 or o3, please note it will make tasks slower.
        "FAST_TOKEN_LIMIT": fast_token_limit,
        "SMART_TOKEN_LIMIT": smart_token_limit,
        "STRATEGIC_TOKEN_LIMIT": strategic_token_limit,
        "BROWSE_CHUNK_MAX_LENGTH": 8192,
        "CURATE_SOURCES": False,
        "SUMMARY_TOKEN_LIMIT": 700,
        "TEMPERATURE": temperature,
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
        "MAX_SEARCH_RESULTS_PER_QUERY": 5,
        "MEMORY_BACKEND": "local",
        "TOTAL_WORDS": total_words,
        "REPORT_FORMAT": "APA",
        "MAX_ITERATIONS": max_iterations,
        "AGENT_ROLE": None,
        "SCRAPER": "bs",
        "MAX_SCRAPER_WORKERS": 15,
        "MAX_SUBTOPICS": 3,
        "LANGUAGE": "english",
        "REPORT_SOURCE": "web",
        "DOC_PATH": "./my-docs",
        "PROMPT_FAMILY": "default",
        "LLM_KWARGS": {},
        "EMBEDDING_KWARGS": {},
        "VERBOSE": False,
        # Deep research specific settings
        "DEEP_RESEARCH_BREADTH": 3,
        "DEEP_RESEARCH_DEPTH": 2,
        "DEEP_RESEARCH_CONCURRENCY": 4,
        # MCP retriever specific settings
        "MCP_SERVERS": [],  # List of predefined MCP server configurations
        "MCP_AUTO_TOOL_SELECTION": True,  # Whether to automatically select the best tool for a query
        "MCP_ALLOWED_ROOT_PATHS": [],  # List of allowed root paths for local file access
        "MCP_STRATEGY": "fast",  # MCP execution strategy: "fast", "deep", "disabled"
        "REASONING_EFFORT": "medium",
    }


def get_researcher(
    query: str,
    provider: Provider,
    model: str,
    similarity_threshold: float = 0.42,
    fast_token_limit: int = 3000,
    smart_token_limit: int = 6000,
    strategic_token_limit: int = 4000,
    temperature: float = 0.4,
    total_words: int = 1200,
    max_iterations: int = 3,
) -> GPTResearcher:
    config = _create_config(
        provider=provider,
        model=model,
        similarity_threshold=similarity_threshold,
        fast_token_limit=fast_token_limit,
        smart_token_limit=smart_token_limit,
        strategic_token_limit=strategic_token_limit,
        temperature=temperature,
        total_words=total_words,
        max_iterations=max_iterations,
    )

    class CustomConfig(Config):

        @override
        @classmethod
        def load_config(cls, config_path: str | None) -> dict[str, Any]:
            """Load a configuration by name."""
            return config

    class CustomGPTResearcher(GPTResearcher):
        @override
        def __init__(
            self,
            query: str,
            report_type: str = ReportType.ResearchReport.value,
            report_format: str = "markdown",
            report_source: str = ReportSource.Web.value,
            tone: Tone = Tone.Objective,
            source_urls: list[str] | None = None,
            document_urls: list[str] | None = None,
            complement_source_urls: bool = False,
            query_domains: list[str] | None = None,
            documents=None,
            vector_store=None,
            vector_store_filter=None,
            config_path=None,
            websocket=None,
            agent=None,
            role=None,
            parent_query: str = "",
            subtopics: list | None = None,
            visited_urls: set | None = None,
            verbose: bool = True,
            context=None,
            headers: dict | None = None,
            max_subtopics: int = 5,
            log_handler=None,
            prompt_family: str | None = None,
            mcp_configs: list[dict] | None = None,
            mcp_max_iterations: int | None = None,
            mcp_strategy: str | None = None,
            **kwargs,
        ):
            """
            Initialize a GPT Researcher instance.

            Args:
                query (str): The research query or question.
                report_type (str): Type of report to generate.
                report_format (str): Format of the report (markdown, pdf, etc).
                report_source (str): Source of information for the report (web, local, etc).
                tone (Tone): Tone of the report.
                source_urls (list[str], optional): List of specific URLs to use as sources.
                document_urls (list[str], optional): List of document URLs to use as sources.
                complement_source_urls (bool): Whether to complement source URLs with web search.
                query_domains (list[str], optional): List of domains to restrict search to.
                documents: Document objects for LangChain integration.
                vector_store: Vector store for document retrieval.
                vector_store_filter: Filter for vector store queries.
                config_path: Path to configuration file.
                websocket: WebSocket for streaming output.
                agent: Pre-defined agent type.
                role: Pre-defined agent role.
                parent_query: Parent query for subtopic reports.
                subtopics: List of subtopics to research.
                visited_urls: Set of already visited URLs.
                verbose (bool): Whether to output verbose logs.
                context: Pre-loaded research context.
                headers (dict, optional): Additional headers for requests and configuration.
                max_subtopics (int): Maximum number of subtopics to generate.
                log_handler: Handler for logging events.
                prompt_family: Family of prompts to use.
                mcp_configs (list[dict], optional): List of MCP server configurations.
                    Each dictionary can contain:
                    - name (str): Name of the MCP server
                    - command (str): Command to start the server
                    - args (list[str]): Arguments for the server command
                    - tool_name (str): Specific tool to use on the MCP server
                    - env (dict): Environment variables for the server
                    - connection_url (str): URL for WebSocket or HTTP connection
                    - connection_type (str): Connection type (stdio, websocket, http)
                    - connection_token (str): Authentication token for remote connections

                    Example:
                    ```python
                    mcp_configs=[{
                        "command": "python",
                        "args": ["my_mcp_server.py"],
                        "name": "search"
                    }]
                    ```
                mcp_strategy (str, optional): MCP execution strategy. Options:
                    - "fast" (default): Run MCP once with original query for best performance
                    - "deep": Run MCP for all sub-queries for maximum thoroughness
                    - "disabled": Skip MCP entirely, use only web retrievers
            """
            self.kwargs = kwargs
            self.query = query
            self.report_type = report_type
            self.cfg = CustomConfig(None)
            self.cfg.set_verbose(verbose)
            self.report_source = (
                report_source
                if report_source
                else getattr(self.cfg, "report_source", None)
            )
            self.report_format = report_format
            self.max_subtopics = max_subtopics
            self.tone = tone if isinstance(tone, Tone) else Tone.Objective
            self.source_urls = source_urls
            self.document_urls = document_urls
            self.complement_source_urls = complement_source_urls
            self.query_domains = query_domains or []
            self.research_sources = (
                []
            )  # The list of scraped sources including title, content and images
            self.research_images = []  # The list of selected research images
            self.documents = documents
            self.vector_store = (
                VectorStoreWrapper(vector_store) if vector_store else None
            )
            self.vector_store_filter = vector_store_filter
            self.websocket = websocket
            self.agent = agent
            self.role = role
            self.parent_query = parent_query
            self.subtopics = subtopics or []
            self.visited_urls = visited_urls or set()
            self.verbose = verbose
            self.context = context or []
            self.headers = headers or {}
            self.research_costs = 0.0
            self.log_handler = log_handler
            self.prompt_family = get_prompt_family(
                prompt_family or self.cfg.prompt_family, self.cfg
            )

            # Process MCP configurations if provided
            self.mcp_configs = mcp_configs
            if mcp_configs:
                self._process_mcp_configs(mcp_configs)

            self.retrievers = get_retrievers(self.headers, self.cfg)
            self.memory = Memory(
                self.cfg.embedding_provider,
                self.cfg.embedding_model,
                **self.cfg.embedding_kwargs,
            )

            # Set default encoding to utf-8
            self.encoding = kwargs.get("encoding", "utf-8")
            self.kwargs.pop(
                "encoding", None
            )  # Remove encoding from kwargs to avoid passing it to LLM calls

            # Initialize components
            self.research_conductor: ResearchConductor = ResearchConductor(self)
            self.report_generator: ReportGenerator = ReportGenerator(self)
            self.context_manager: ContextManager = ContextManager(self)
            self.scraper_manager: BrowserManager = BrowserManager(self)
            self.source_curator: SourceCurator = SourceCurator(self)
            self.deep_researcher: DeepResearchSkill | None = None
            if report_type == ReportType.DeepResearch.value:
                self.deep_researcher = DeepResearchSkill(self)

            # Handle MCP strategy configuration with backwards compatibility
            self.mcp_strategy = self._resolve_mcp_strategy(
                mcp_strategy, mcp_max_iterations
            )

    return CustomGPTResearcher(
        query=query, report_type="research_report", config=config
    )
