# Docker Image for LLM-powered CI/CD pipeline steps

[![Generic badge](https://img.shields.io/badge/RHEL-8_Python_3.11-green.svg)](https://teambank.jfrog.io/ui/packages/docker:%2F%2Frhel?name=rhel&type=packages)
[![Build Status](https://dev.azure.com/teambankag/CDOS/_apis/build/status%2Fdocker-images%2Fdocker-image-llm-runtime?repoName=docker-image-llm-runtime&branchName=main)](https://dev.azure.com/teambankag/CDOS/_build/latest?definitionId=3770&repoName=docker-image-llm-runtime&branchName=main)
[![Generic badge](https://img.shields.io/badge/Managed_by-IT-black)]()
[![Generic badge](https://img.shields.io/badge/Cloud_allowed-Yes-green)](https://wiki.teambank.de/confluence/x/bR9zHw)


### Available platforms
![Platform linux/amd64](https://img.shields.io/badge/linux/amd64-ready-green)
![Platform linux/arm64](https://img.shields.io/badge/linux/arm64-ready-green)

## This repo is a fork of [ai-first-devops-toolkit](https://github.com/Nantero1/ai-first-devops-toolkit) and the resulting pypi package [llm-ci-runner repository](https://pypi.org/project/llm-ci-runner/).

Is is currently used to run AI-powered CI/CD pipeline steps. For usage refer to the [pipeline templates](https://dev.azure.com/teambankag/CDOS/_git/azure-devops-pipeline).

You can use this Docker image directly as a container in your Azure DevOps pipeline jobs to enable AI-powered automation steps. When your pipeline runs inside this image, all the required dependencies for LLM-based automation are pre-installed and ready to use.

**Example: Using this image in Azure DevOps pipeline**

```yaml
jobs:
  - job: ai_automation
    displayName: "Run AI Automation with LLM Runtime"
    container: 
      image: teambank.jfrog.io/cdos-marketplace-docker/llm-runtime:latest
    steps:
      - script: |
          uv run llm_ci_runner.py \
            --input-file examples/02-devops/pr-description/input.json \
            --schema-file examples/02-devops/pr-description/schema.json \
            --output-file pr-analysis.json
          pr_description=$(cat pr-analysis.json | jq '.response.description')
          echo vso[task.setvariable variable=pr_description]$pr_description
        displayName: "Run LLM CI Runner for PR Analysis"
# if not set sane defaults are used at the moment
#        env:
#          AZURE_OPENAI_ENDPOINT: $(AZURE_OPENAI_ENDPOINT)
#          AZURE_OPENAI_MODEL: $(AZURE_OPENAI_MODEL)
#          AZURE_OPENAI_API_VERSION: $(AZURE_OPENAI_API_VERSION)

```

This approach allows you to:
- Run AI-powered code review, changelog generation, security analysis, and more as part of your CI/CD pipeline
- Guarantee schema-compliant outputs for downstream automation
- Leverage Azure RBAC or API key authentication for secure access to Azure OpenAI
- Use all features of the `llm-ci-runner` CLI and Python module out-of-the-box

See the [pipeline templates](https://dev.azure.com/teambankag/CDOS/_git/azure-devops-pipeline) for more details on how this image is used to automate CI/CD workflows.

Below is the original README.md:

---

# AI-First Toolkit: LLM-Powered Automation

[![PyPI version](https://badge.fury.io/py/llm-ci-runner.svg)](https://badge.fury.io/py/llm-ci-runner) [![CI](https://github.com/Nantero1/ai-first-devops-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/Nantero1/ai-first-devops-toolkit/actions/workflows/ci.yml) [![Unit Tests](https://github.com/Nantero1/ai-first-devops-toolkit/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/Nantero1/ai-first-devops-toolkit/actions/workflows/unit-tests.yml) [![Coverage badge](https://raw.githubusercontent.com/Nantero1/ai-first-devops-toolkit/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/Nantero1/ai-first-devops-toolkit/blob/python-coverage-comment-action-data/htmlcov/index.html) [![CodeQL](https://github.com/Nantero1/ai-first-devops-toolkit/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/Nantero1/ai-first-devops-toolkit/actions/workflows/github-code-scanning/codeql) [![License: MIT](https://img.shields.io/badge/License-MIT-brightgreen.svg)](https://opensource.org/licenses/MIT) [![MyPy](https://img.shields.io/badge/mypy-checked-brightgreen)](http://mypy-lang.org/) [![Ruff](https://img.shields.io/badge/ruff-checked-brightgreen)](https://github.com/astral-sh/ruff) [![OpenSSF Best Practices](https://www.bestpractices.dev/projects/10922/badge)](https://www.bestpractices.dev/projects/10922) [![Downloads](https://img.shields.io/pypi/dm/llm-ci-runner)](https://www.pepy.tech/projects/llm-ci-runner)

> **🚀 The Future of DevOps is AI-First**  
> This toolkit represents a step toward [AI-First DevOps](https://technologyworkroom.blogspot.com/2025/06/building-ai-first-devops.html) - where intelligent automation handles the entire development lifecycle. Built for teams ready to embrace the exponential productivity gains of AI-powered development. Please read [the blog post](https://technologyworkroom.blogspot.com/2025/06/building-ai-first-devops.html) for more details on the motivation.

## TLDR: What This Tool Does

**Purpose**: Transform any unstructured business knowledge into reliable, structured data that powers intelligent automation across your entire organization.

**Perfect For**:
- 🏦 **Financial Operations**: Convert loan applications, audits, and regulatory docs into structured compliance data
- 🏥 **Healthcare Systems**: Transform patient records, clinical notes, and research data into medical formats  
- ⚖️ **Legal & Compliance**: Process contracts, court docs, and regulatory texts into actionable risk assessments
- 🏭 **Supply Chain**: Turn logistics reports, supplier communications, and forecasts into optimization insights
- 👥 **Human Resources**: Convert resumes, performance reviews, and feedback into structured talent analytics
- 🛡️ **Security Operations**: Transform threat reports, incident logs, and assessments into standard frameworks
- 🚀 **DevOps & Engineering**: Use commit logs, deployment reports, and system logs for automated AI actions
- 🔗 **Enterprise Integration**: Connect any business process to downstream systems with guaranteed consistency
---

### Simple structured output example

```bash
# Install and use immediately
pip install llm-ci-runner
llm-ci-runner --input-file examples/02-devops/pr-description/input.json --schema-file examples/02-devops/pr-description/schema.json
```
![Structured output of the PR review example](https://github.com/Nantero1/ai-first-devops-toolkit/raw/main/examples/02-devops/pr-description/output.png)

## The AI-First Development Revolution

This toolkit embodies the principles outlined in [Building AI-First DevOps](https://technologyworkroom.blogspot.com/2025/06/building-ai-first-devops.html):

| Traditional DevOps          | AI-First DevOps (This Tool)                        |
| --------------------------- | -------------------------------------------------- |
| Manual code reviews         | 🤖 AI-powered reviews with structured findings      |
| Human-written documentation | 📝 AI-generated docs with guaranteed consistency    |
| Reactive security scanning  | 🔍 Proactive AI security analysis                   |
| Manual quality gates        | 🎯 AI-driven validation with schema enforcement     |
| Linear productivity         | 📈 Exponential gains through intelligent automation |

## Features

- 🎯 **100% Schema Enforcement**: Your pipeline never gets invalid data. Token-level schema enforcement with guaranteed compliance
- 🔄 **Resilient execution**: Retries with exponential back-off and jitter plus a clear exception hierarchy keep transient cloud faults from breaking your CI.
- 🚀 **Zero-Friction CLI**: Single script, minimal configuration for pipeline integration and automation
- 🔐 **Enterprise Security**: Azure RBAC via DefaultAzureCredential with fallback to API Key
- 📦 **CI-friendly CLI**: Stateless command that reads JSON/YAML, writes JSON/YAML, and exits with proper codes
- 🎨 **Beautiful Logging**: Rich console output with timestamps and colors
- 📁 **File-based I/O**: CI/CD friendly with JSON/YAML input/output
- 📋 **Template-Driven Workflows**: Handlebars and Jinja2 templates with YAML variables for dynamic prompt generation
- 📄 **YAML Support**: Use YAML for schemas, input files, and output files - more readable than JSON
- 🔧 **Simple & Extensible**: Easy to understand and modify for your specific needs
- 🤖 **Semantic Kernel foundation**: async, service-oriented design ready for skills, memories, orchestration, and future model upgrades
- 📚 **Documentation**: Comprehensive documentation for all features and usage examples. Use your semantic kernel skills to extend the functionality.
- 🧑‍⚖️ **Acceptance Tests**: pytest framework with the LLM-as-Judge pattern for quality gates. Test your scripts before you run them in production.
- 💰 **Coming soon**: token usage and cost estimation appended to each result for budgeting and optimisation

## 🚀 The Only Enterprise AI DevOps Tool That Delivers RBAC Security, Robustness and Simplicity

**LLM-CI-Runner stands alone in the market** as the only tool combining **100% schema enforcement**, **enterprise RBAC authentication**, and robust **Semantic Kernel integration with templates** in a single CLI solution. **No other tool delivers all three critical enterprise requirements together**.

## Installation

```bash
pip install llm-ci-runner
```

That's it! No complex setup, no dependency management - just install and use. Perfect for CI/CD pipelines and local development.

## Quick Start

### 1. Install from PyPI

```bash
pip install llm-ci-runner
```

### 2. Set Environment Variables

**Azure OpenAI (Priority 1):**
```bash
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_MODEL="gpt-4.1-nano"  # or any other GPT deployment name
export AZURE_OPENAI_API_VERSION="2024-12-01-preview"  # Optional
```

**OpenAI (Fallback):**
```bash
export OPENAI_API_KEY="your-very-secret-api-key"
export OPENAI_CHAT_MODEL_ID="gpt-4.1-nano"  # or any OpenAI model
export OPENAI_ORG_ID="org-your-org-id"  # Optional
```

**Authentication Options:**
- **Azure RBAC (Recommended)**: Uses `DefaultAzureCredential` for Azure RBAC authentication - no API key needed! See [Microsoft Docs](https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.defaultazurecredential?view=azure-python) for setup.
- **Azure API Key**: Set `AZURE_OPENAI_API_KEY` environment variable if not using RBAC.
- **OpenAI API Key**: Required for OpenAI fallback when Azure is not configured.

**Priority**: Azure OpenAI takes priority when both Azure and OpenAI environment variables are present.

### 3a. Basic Usage

```bash
# Simple chat example
llm-ci-runner --input-file examples/01-basic/simple-chat/input.json

# With structured output schema
llm-ci-runner \
  --input-file examples/01-basic/sentiment-analysis/input.json \
  --schema-file examples/01-basic/sentiment-analysis/schema.json

# Custom output file
llm-ci-runner \
  --input-file examples/02-devops/pr-description/input.json \
  --schema-file examples/02-devops/pr-description/schema.json \
  --output-file pr-analysis.json

# YAML input files (alternative to JSON)
llm-ci-runner \
  --input-file config.yaml \
  --schema-file schema.yaml \
  --output-file result.yaml
```

### 3b. Template-Based Workflows

**Dynamic prompt generation with YAML, Handlebars or Jinja2 templates:**

```bash
# Handlebars template example
llm-ci-runner \
  --template-file examples/05-templates/handlebars-template/template.hbs \
  --template-vars examples/05-templates/handlebars-template/template-vars.yaml \
  --schema-file examples/05-templates/handlebars-template/schema.yaml \
  --output-file handlebars-result.yaml
  
# Or using Jinja2 templates
llm-ci-runner \
  --template-file examples/05-templates/jinja2-template/template.j2 \
  --template-vars examples/05-templates/jinja2-template/template-vars.yaml \
  --schema-file examples/05-templates/jinja2-template/schema.yaml \
  --output-file jinja2-result.yaml
```

For more examples see the [examples directory](https://github.com/Nantero1/ai-first-devops-toolkit/tree/main/examples).

**Benefits of Template Approach:**
- 🎯 **Reusable Templates**: Create once, use across multiple scenarios
- 📝 **YAML Configuration**: More readable than JSON for complex setups
- 🔄 **Dynamic Content**: Variables and conditional rendering
- 🚀 **CI/CD Ready**: Perfect for parameterized pipeline workflows

### 4. Development Setup (Optional)

For contributors or advanced users who want to modify the source:

```bash
# Install UV if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install for development
git clone https://github.com/Nantero1/ai-first-devops-toolkit.git
cd ai-first-devops-toolkit
uv sync

# Run from source
uv run llm-ci-runner --input-file examples/01-basic/simple-chat/input.json
```

## The AI-First Transformation: Why Unstructured → Structured Matters

LLMs excel at extracting meaning from messy text, logs, documents, and mixed-format data, then emitting **schema-compliant JSON/YAML** that downstream systems can trust. This unlocks:

- **🔄 Straight-Through Processing**: Structured payloads feed BI dashboards, RPA robots, and CI/CD gates without human parsing
- **🎯 Context-Aware Decisions**: LLMs fuse domain knowledge with live telemetry to prioritize incidents, forecast demand, and spot security drift
- **📋 Auditable Compliance**: Formal outputs make it easy to track decisions for regulators and ISO/NIST audits
- **⚡ Rapid Workflow Automation**: Enable automation across customer service, supply-chain planning, HR case handling, and security triage
- **🔗 Safe Pipeline Composition**: Structured contracts let AI-first pipelines remain observable and composable while capitalizing on unstructured enterprise data


## Input Formats

### Traditional JSON Input

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user", 
      "content": "Your task description here"
    }
  ],
  "context": {
    "session_id": "optional-session-id",
    "metadata": {
      "any": "additional context"
    }
  }
}
```

### YAML Input

```yaml
messages:
  - role: system
    content: "You are a helpful assistant."
  - role: user
    content: "Your task description here"
context:
  session_id: "optional-session-id"
  metadata:
    any: "additional context"
```

### Template-Based Input

**Handlebars Template** (`template.hbs`):
```handlebars
<message role="system">
You are an expert {{expertise.domain}} engineer.
Focus on {{expertise.focus_areas}}.
</message>

<message role="user">
Analyze this {{task.type}}:

{{#each task.items}}
- {{this}}
{{/each}}

Requirements: {{task.requirements}}
</message>
```

**Jinja2 Template** (`template.j2`):
```jinja2
<message role="system">
You are an expert {{expertise.domain}} engineer.
Focus on {{expertise.focus_areas}}.
</message>

<message role="user">
Analyze this {{task.type}}:

{% for item in task.items %}
- {{item}}
{% endfor %}

Requirements: {{task.requirements}}
</message>
```

**Template Variables** (`vars.yaml`):
```yaml
expertise:
  domain: "DevOps"
  focus_areas: "security, performance, maintainability"
task:
  type: "pull request"
  items:
    - "Changed authentication logic"
    - "Updated database queries"
    - "Added input validation"
  requirements: "Focus on security vulnerabilities"
```

## Structured Outputs with 100% Schema Enforcement

When you provide a `--schema-file`, the runner guarantees perfect schema compliance:

```bash
llm-ci-runner \
  --input-file examples/01-basic/sentiment-analysis/input.json \
  --schema-file examples/01-basic/sentiment-analysis/schema.json
```

**Note**: Output defaults to `result.json`. Use `--output-file custom-name.json` for custom output files.

**Supported Schema Features**:
✅ String constraints (enum, minLength, maxLength, pattern)  
✅ Numeric constraints (minimum, maximum, multipleOf)  
✅ Array constraints (minItems, maxItems, items type)  
✅ Required fields enforced at generation time  
✅ Type validation (string, number, integer, boolean, array)  

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Setup Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.12'

- name: Install LLM CI Runner
  run: pip install llm-ci-runner

- name: Generate PR Review with Templates
  run: |
    llm-ci-runner \
      --template-file .github/templates/pr-review.j2 \
      --template-vars pr-context.yaml \
      --schema-file .github/schemas/pr-review.yaml \
      --output-file pr-analysis.yaml
  env:
    AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
    AZURE_OPENAI_MODEL: ${{ secrets.AZURE_OPENAI_MODEL }}
```

For complete CI/CD examples, see **[examples/uv-usage-example.md](https://github.com/Nantero1/ai-first-devops-toolkit/blob/main/examples/uv-usage-example.md)**. This repo is also using itself for release note generation, **check it out [here](https://github.com/Nantero1/ai-first-devops-toolkit/blob/c4066d347ae14d37cb674e36007a678f38b36439/.github/workflows/release.yml#L145-L149)**.

## Authentication

**Azure OpenAI**: Uses Azure's `DefaultAzureCredential` supporting:
- Environment variables (local development)
- Managed Identity (recommended for Azure CI/CD)
- Azure CLI (local development)
- Service Principal (non-Azure CI/CD)

**OpenAI**: Uses API key authentication with optional organization ID.


## Testing

We maintain comprehensive test coverage with **100% success rate**:

```bash
# For package users - install test dependencies
pip install llm-ci-runner[dev]

# For development - install from source with test dependencies
uv sync --group dev

# Run specific test categories
pytest tests/unit/ -v          # 70 unit tests
pytest tests/integration/ -v   # End-to-end examples
pytest acceptance/ -v          # LLM-as-judge evaluation

# Or with uv for development
uv run pytest tests/unit/ -v
uv run pytest tests/integration/ -v
uv run pytest acceptance/ -v
```

## Architecture

Built on **Microsoft Semantic Kernel** for:
- Enterprise-ready Azure OpenAI and OpenAI integration
- Future-proof model compatibility
- **100% Schema Enforcement**: KernelBaseModel integration with token-level constraints
- **Dynamic Model Creation**: Runtime JSON schema → Pydantic model conversion
- **Azure RBAC**: Azure RBAC via DefaultAzureCredential
- **Automatic Fallback**: Azure-first priority with OpenAI fallback

## The AI-First Development Journey

This toolkit is your first step toward [AI-First DevOps](https://technologyworkroom.blogspot.com/2025/06/building-ai-first-devops.html). As you integrate AI into your development workflows, you'll experience:

1. **🚀 Exponential Productivity**: AI handles routine tasks while you focus on architecture
2. **🎯 Guaranteed Quality**: Schema enforcement eliminates validation errors
3. **🤖 Autonomous Operations**: AI agents make decisions in your pipelines
4. **📈 Continuous Improvement**: Every interaction improves your AI system

**The future belongs to teams that master AI-first principles.** This toolkit gives you the foundation to start that journey today.

## Real-World Examples

You can explore the **[examples directory](https://github.com/Nantero1/ai-first-devops-toolkit/tree/main/examples)** for a complete collection of self-contained examples organized by category.

For comprehensive real-world CI/CD scenarios, see **[examples/uv-usage-example.md](https://github.com/Nantero1/ai-first-devops-toolkit/blob/main/examples/uv-usage-example.md)**. 

### 100 AI Automation Use Cases for AI-First Automation

**DevOps & Engineering** 🔧

1. 🤖 AI-generated PR review – automated pull request analysis with structured review findings
2. 📝 Release note composer – map commits to semantic-version bump rules and structured changelogs
3. 🔍 Vulnerability scanner – map code vulnerabilities to OWASP standards with actionable remediation
4. ☸️ Kubernetes manifest optimizer – produce risk-scored diffs and security hardening recommendations
5. 📊 Log anomaly triager – convert system logs into OTEL-formatted events for SIEM ingestion  
6. 💰 Cloud cost explainer – output tagged spend by team in FinOps schema for budget optimization
7. 🔄 API diff analyzer – produce backward-compatibility scorecards from specification changes
8. 🛡️ IaC drift detector – turn Terraform plans into CVE-linked security findings
9. 📋 Dependency license auditor – emit SPDX-compatible reports for compliance tracking
10. 🎯 SLA breach summarizer – file structured JIRA tickets with SMART action items

**Governance, Risk & Compliance** 🏛️

11. 📊 Regulatory delta analyzer – emit change-impact matrices from new compliance requirements
12. 🌱 ESG report synthesizer – map CSR prose to GRI indicators and sustainability metrics
13. 📋 SOX-404 narrative converter – transform controls descriptions into testable audit checklists  
14. 🏦 Basel III stress-test interpreter – output capital risk buckets from regulatory scenarios
15. 🕵️ AML SAR formatter – convert investigator notes into Suspicious Activity Report structures
16. 🔒 Privacy policy parser – generate GDPR data-processing-activity logs from legal text
17. 🔍 Internal audit evidence linker – export control traceability graphs for compliance tracking
18. 📊 Carbon emission disclosure normalizer – structure sustainability data into XBRL taxonomy
19. ⚖️ Regulatory update tracker – generate structured compliance action items from guideline changes
20. 🛡️ Safety inspection checker – transform narratives into OSHA citation checklists

**Financial Services** 🏦

21. 🏦 Loan application analyzer – transform free-text applications into Basel-III risk-model inputs
22. 📊 Earnings call sentiment quantifier – output KPI deltas and investor sentiment scores
23. 💹 Budget variance explainer – produce drill-down pivot JSON for financial analysis
24. 📈 Portfolio risk dashboard builder – feed VaR models with structured investment analysis
25. 💳 Fraud alert generator – map investigation notes to CVSS-scored security metrics
26. 💰 Treasury cash-flow predictor – ingest email forecasts into structured planning models
27. 📊 Financial forecaster – summarize reports into structured cash-flow and projection objects
28. 🧾 Invoice processor – convert receipts into double-entry ledger posts with GAAP tags
29. 📋 Stress test scenario packager – structure regulatory submission data for banking compliance
30. 🏦 Insurance claim assessor – return structured claim-decision objects with risk scores

**Healthcare & Life Sciences** 🏥

31. 🏥 Patient intake processor – build HL7/FHIR-compliant patient records from free-form intake forms
32. 🧠 Mental health triage assistant – structure referral notes with priority classifications and care pathways
33. 📊 Radiology report coder – output SNOMED-coded JSON from diagnostic imaging narratives
34. 💊 Clinical trial note packager – create FDA eCTD modules from research documentation
35. 📋 Prescription parser – turn text prescriptions into structured e-Rx objects with dosage validation
36. ⚡ Vital sign anomaly summarizer – generate alert reports with clinical priority rankings
37. 🧪 Lab result organizer – output LOINC-coded tables from diagnostic test narratives
38. 🏥 Medical device log summarizer – generate UDI incident files for regulatory reporting
39. 📈 Patient feedback sentiment analyzer – feed quality-of-care KPIs from satisfaction surveys
40. 👩‍⚕️ Clinical observation compiler – convert research notes into structured data for trials

**Legal & Compliance** ⚖️

41. 🏛️ Legal contract parser – extract clauses and compute risk scores from contract documents
42. 📝 Court opinion digest – summarize judicial opinions into structured precedent and citation graphs
43. 🏛️ Legal discovery summarizer – extract key issues and risks from large document sets
44. 💼 Contract review summarizer – extract risk factors and key dates from legal contracts
45. 🏛️ Policy impact assessor – convert policy proposals into stakeholder impact matrices
46. 📜 Patent novelty comparator – produce claim-overlap matrices from prior art analysis
47. 🏛️ Legal bill auditor – transform billing details into itemized expense and compliance reports
48. 📋 Case strategy brainstormer – summarize likely arguments from litigation documentation
49. 💼 Legal email analyzer – extract key issues and deadlines from email threads for review
50. ⚖️ Expert witness report normalizer – create citation-linked outlines from testimony records

**Customer Experience & Sales** 🛒

51. 🎧 Tier-1 support chatbot – convert customer queries into tickets with reproducible troubleshooting steps  
52. ⭐ Review sentiment miner – produce product-feature tallies from customer feedback analysis
53. 📉 Churn risk email summarizer – export CRM risk scores from customer communication patterns
54. 🗺️ Omnichannel conversation unifier – generate customer journey maps from multi-platform interactions
55. ❓ Dynamic FAQ builder – structure knowledge base content from community forum discussions
56. 📋 Proposal auto-grader – output RFP compliance matrices with scoring rubrics
57. 📈 Upsell opportunity extractor – create lead-scoring JSON from customer interaction analysis
58. 📱 Social media crisis detector – feed escalation playbooks with brand sentiment monitoring
59. 🌐 Multilingual intent router – tag customer chats to appropriate support queues by language/topic
60. 🎯 Marketing copy generator – create brand-compliant content with tone and messaging constraints

**HR & People Operations** 👥

61. 📄 CV-to-JD matcher – rank candidates with explainable competency scores and fit analysis
62. 🎤 Interview transcript summarizer – export structured competency rubrics with evaluation criteria
63. ✅ Onboarding policy compliance checker – produce new-hire checklist completion tracking
64. 📊 Performance review sentiment analyzer – create growth-plan JSON with development recommendations
65. 💰 Payroll inquiry classifier – map employee emails to structured case codes for HR processing
66. 🏥 Benefits Q&A automation – generate eligibility responses from policy documentation
67. 🚪 Exit interview insight extractor – feed retention dashboards with structured departure analytics
68. 📚 Training content gap mapper – align job roles to skill taxonomies for learning programs
69. 🛡️ Workplace incident processor – convert safety reports into OSHA 301 compliance records
70. 📊 Diversity metric synthesizer – summarize inclusion survey data into actionable insights

**Supply Chain & Manufacturing** 🏭

71. 📊 Demand forecast summarizer – output SKU-level predictions from market analysis and sales data
72. 📋 Purchase order processor – convert supplier communications into structured ERP line-items
73. 🌱 Supplier risk scanner – generate ESG compliance scores from vendor assessment reports
74. 🔧 Predictive maintenance log analyst – produce work orders from equipment telemetry narratives
75. 🚛 Logistics delay explainer – return route-change suggestions from transportation disruption reports
76. ♻️ Circular economy return classifier – create refurbishment tags from product return descriptions
77. 🌍 Carbon footprint calculator – map transport legs to CO₂e emissions for sustainability reporting
78. 📦 Safety stock alert generator – output inventory triggers with lead-time assumptions
79. 📜 Regulatory import/export harmonizer – produce HS-code sheets from trade documentation
80. 🏭 Production yield analyzer – generate efficiency reports from manufacturing floor logs

**Security & Risk Management** 🔒

81. 🛡️ MITRE ATT&CK mapper – translate IDS alerts into tactic-technique JSON for threat intelligence
82. 🎣 Phishing email extractor – produce IOC STIX bundles from security incident reports
83. 🔐 Zero-trust policy generator – convert narrative access requests into structured policy rules
84. 🚨 SOC alert deduplicator – cluster security tickets by kill-chain stage for efficient triage
85. 🏴‍☠️ Red team debrief summarizer – export OWASP Top-10 gaps from penetration test reports
86. 📋 Data breach notifier – craft GDPR-compliant disclosure packets with timeline and impact data
87. 🧠 Threat intel feed normalizer – convert mixed security PDFs into MISP threat objects
88. 🔍 Secret leak scanner – output GitHub code-owner mentions from repository security scans
89. 📊 Vendor risk questionnaire scorer – generate SIG Lite security assessment answers
90. 🏗️ Security audit tracker – link ISO-27001 controls to evidence artifacts for compliance

**Knowledge & Productivity** 📚

91. 🎙️ Meeting transcript processor – extract action items with owners and deadlines into project tracking JSON
92. 📚 Research paper summarizer – export citation graphs and key findings for literature review databases
93. 📋 SOP generator – convert process narratives into step-by-step validation checklists
94. 🔄 Code diff summarizer – generate reviewer hints and impact analysis from version control changes  
95. 📊 API changelog analyzer – produce backward-compatibility scorecards for development teams
96. 🧠 Mind map creator – structure brainstorming sessions into hierarchical knowledge trees
97. 📖 Knowledge base gap detector – suggest article stubs from frequently asked questions analysis
98. 🎯 Personal OKR journal parser – output progress dashboards with milestone tracking
99. 💼 White paper composer – transform technical discussions into structured thought leadership content
100. 🧩 Universal transformer – convert any unstructured domain knowledge into your custom schema-validated JSON


## License

MIT License - See [LICENSE](https://github.com/Nantero1/ai-first-devops-toolkit/blob/main/LICENSE) file for details. Copyright (c) 2025, Benjamin Linnik.

## Support

**🐛 Found a bug? 💡 Have a question? 📚 Need help?**

**GitHub is your primary destination for all support:**

- **📋 Issues & Bug Reports**: [Create an issue](https://github.com/Nantero1/ai-first-devops-toolkit/issues)
- **📖 Documentation**: [Browse examples](https://github.com/Nantero1/ai-first-devops-toolkit/tree/main/examples)
- **🔧 Source Code**: [View source](https://github.com/Nantero1/ai-first-devops-toolkit)

**Before opening an issue, please:**
1. ✅ Check the [examples directory](https://github.com/Nantero1/ai-first-devops-toolkit/tree/main/examples) for solutions
2. ✅ Review the error logs (beautiful output with Rich!)
3. ✅ Validate your Azure authentication and permissions
4. ✅ Ensure your input JSON follows the required format
5. ✅ Search existing [issues](https://github.com/Nantero1/ai-first-devops-toolkit/issues) for similar problems

**Quick Links:**
- 🚀 [Getting Started Guide](https://github.com/Nantero1/ai-first-devops-toolkit#quick-start)
- 📚 [Complete Examples](https://github.com/Nantero1/ai-first-devops-toolkit/tree/main/examples)
- 🔧 [CI/CD Integration](https://github.com/Nantero1/ai-first-devops-toolkit#cicd-integration)
- 🎯 [Use Cases](https://github.com/Nantero1/ai-first-devops-toolkit#use-cases)

---

*Ready to embrace the AI-First future? Start with this toolkit and build your path to exponential productivity. Learn more about the AI-First DevOps revolution in [Building AI-First DevOps](https://technologyworkroom.blogspot.com/2025/06/building-ai-first-devops.html).*
