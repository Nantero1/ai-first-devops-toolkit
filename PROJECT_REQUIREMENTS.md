<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

## Vision: Fully-Automated LLM Utilities for CI/CD

We want a **single, self-service toolkit** that lets any engineer drop a tiny Python script into a pipeline step and immediately gain large-language-model super-powers—without becoming AI experts, without storing secrets in YAML, and without worrying whether tomorrow’s GPT-5 breaks their code.

### Key Objectives

- **Zero-friction CLI scripts**: one file, one command, runs anywhere Azure CLI and Python 3.11+ are available.
- **Enterprise security**: RBAC via `DefaultAzureCredential`, no API keys.
- **Re-usable building blocks**: a universal *LLM runner* and an *Agent runner* that share logging, error handling, and output conventions.
- **Strict, machine-readable outputs**: JSON or Pydantic-validated objects so downstream tasks can parse results deterministically.
- **Future-proofing**: written on Microsoft Semantic Kernel (SK) because it tracks Azure OpenAI changes, supports GPT-4.1, GPT-4o, and upcoming models on day 1.


## High-Level Architecture

| Layer | Component | Responsibility |
| :-- | :-- | :-- |
| CI/CD Platform | GitHub Actions / Azure Pipelines | Mounts container with Python \& AZ CLI; executes scripts |
| Python Toolkit | `sk_universal.py` | Stateless, single-shot LLM call from CLI arguments |
| Python Toolkit | `sk_agent.py` | Stateful agent that can call tools (Jira, GitHub, FS, etc.) |
| Plugins | Native Python classes or OpenAPI specs | Expose actions (e.g., `create_jira_ticket`) to the agent |
| Azure Services | Azure OpenAI, Managed Identity, Key Vault | Compute, auth, secrets, model hosting |
| Observability | Structured log files, optional Application Insights | Debug and audit every run |

## Script 1 — `sk_universal.py`

| Feature | Spec |
| :-- | :-- |
| Invocation | `python sk_universal.py --model gpt-4.1 --endpoint https://*.openai.azure.com --messages '<json>' --output-file result.json [--structured-output '<json-schema>'] [--temperature 0.2]` |
| Authentication | `DefaultAzureCredential` → bearer token → Azure OpenAI |
| Input 1: Context | JSON array of  objects; loaded directly into `KernelArguments(**json.loads(arg))` |
| Input 2: Structured Output (optional) | JSON schema → dynamic Pydantic model generated at runtime and passed via `response_format` |
| Logging | Stdout` |
| Output | If schema provided → JSON object that validates; else raw assistant text. Always written to `--output-file` |

**Guarantees**

1. Fails fast if JSON cannot be parsed or model rejects schema.
2. Always exits with non-zero code on validation errors so pipeline can gate.
3. Uses environment variables (`AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_MODEL`) as fallbacks for brevity


## Shared Python Package (`ai_cicd_helpers`)

| Module | Purpose |
| :-- | :-- |
| `auth.py` | Central `get_default_chat_service(model, endpoint)` using RBAC |
| `logging_cfg.py` | Standardised logging formatter + rotating files |
| `schema_utils.py` | Build Pydantic models from JSON schema strings |
| `history_utils.py` | `to_chat_history(json_str)` and `serialize(history)` |
| `error.py` | Custom exceptions mapped to exit codes |

Importing these helpers keeps both top-level scripts <200 LOC.

## Non-Functional Requirements

- **Performance**: cold-start < 1 s; streaming responses when `--stream` flag passed.
- **Scalability**: container image is stateless; horizontal scale in runners.
- **Security**: only outbound to Azure OpenAI and SaaS APIs; no inbound ports.
- **Maintainability**: typed code, docstrings, unit tests with pytest; scripts published to internal PyPI.
- **Documentation**: Markdown README with quick-starts, env-var matrix, troubleshooting.
- **Licensing**: MIT internally; note SK’s MIT licence and Jira/GitHub SDK licences.


## Future Extensions

1. **History Summarisation**: plug in `ChatHistoryReducer` once prompts hit token limits.
2. **Vector Memory**: optional Cosmos DB or Azure AI Search for long-term memories.
3. **Additional Tools**: SonarQube, Slack, ServiceNow via OpenAPI import—no code changes in agent.
4. **Self-updating Container**: nightly rebuild picks latest Semantic Kernel release for model parity.
5. **Metrics**: push latency and token counts to Prometheus via statsd exporter.

## Deliverables Checklist

| Deliverable | Owner | Status |
| :-- | :-- | :-- |
| `sk_universal.py` | AI Platform team | ⏳ |
| Shared package `ai_cicd_helpers` | AI Platform team | ⏳ |
| Dockerfile \& ghcr.io image | DevOps | ⏳ |
| Example pipeline YAML | DevOps | 🔜 |
| README \& API docs | Tech Writing | 🔜 |
| Security review (RBAC, secrets) | SecOps | 🔜 |
| Performance baseline report | QA | 🔜 |

### Bottom Line

With these two thin but powerful scripts—and the surrounding helper library—we satisfy every requirement discussed:

- **Ease of use**: one-liner CLI, JSON in/out.
- **Agent power**: complex multi-tool workflows when needed.
- **Enterprise safety**: RBAC, structured outputs, deterministic failures.
- **Future-proof**: built on Microsoft Semantic Kernel, ready for GPT-4.x and 5.0 drops.

This foundation turns LLM features into just another pipeline utility—stable, testable, and ready for production.

