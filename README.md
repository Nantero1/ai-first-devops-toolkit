# AI-First Toolkit: LLM-Powered Automation

[![PyPI version](https://badge.fury.io/py/llm-ci-runner.svg)](https://badge.fury.io/py/llm-ci-runner) [![CI](https://github.com/Nantero1/ai-first-devops-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/Nantero1/ai-first-devops-toolkit/actions/workflows/ci.yml) [![Unit Tests](https://github.com/Nantero1/ai-first-devops-toolkit/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/Nantero1/ai-first-devops-toolkit/actions/workflows/unit-tests.yml) [![Coverage badge](https://raw.githubusercontent.com/Nantero1/ai-first-devops-toolkit/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/Nantero1/ai-first-devops-toolkit/blob/python-coverage-comment-action-data/htmlcov/index.html) [![CodeQL](https://github.com/Nantero1/ai-first-devops-toolkit/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/Nantero1/ai-first-devops-toolkit/actions/workflows/github-code-scanning/codeql)

> **🚀 The Future of DevOps is AI-First**  
> This toolkit represents a step toward [AI-First DevOps](https://technologyworkroom.blogspot.com/2025/06/building-ai-first-devops.html) - where intelligent automation handles the entire development lifecycle. Built for teams ready to embrace the exponential productivity gains of AI-powered development. Please read [the blog post](https://technologyworkroom.blogspot.com/2025/06/building-ai-first-devops.html) for more details on the motivation.

## TLDR: What This Tool Does

**Purpose**: Zero-friction LLM integration for pipelines with **100% guaranteed schema compliance**. This is your foundation for AI-first integration practices.

**Perfect For**:
- 🤖 **AI-Generated Code Reviews**: Automated PR analysis with structured findings
- 📝 **Intelligent Documentation**: Generate changelogs, release notes, and docs automatically  
- 🔍 **Security Analysis**: AI-powered vulnerability detection with structured reports
- 🎯 **Quality Gates**: Enforce standards through AI-driven validation
- 🚀 **Autonomous Development**: Enable AI agents to make decisions in your pipelines
- 🎯 **JIRA Ticket Updates**: Update JIRA tickets based on LLM output
- 🔗 **Unlimited Integration Possibilities**: Chain it multiple times and use as glue code in your tool stack
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

| Traditional DevOps | AI-First DevOps (This Tool) |
|-------------------|----------------------------|
| Manual code reviews | 🤖 AI-powered reviews with structured findings |
| Human-written documentation | 📝 AI-generated docs with guaranteed consistency |
| Reactive security scanning | 🔍 Proactive AI security analysis |
| Manual quality gates | 🎯 AI-driven validation with schema enforcement |
| Linear productivity | 📈 Exponential gains through intelligent automation |

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

For more examples see the [examples directory](https://github.com/Nantero1/ai-first-devops-toolkit/tree/main/examples/05-templates).

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

## Real-World Examples

You can explore the **[examples directory](https://github.com/Nantero1/ai-first-devops-toolkit/tree/main/examples)** for a complete collection of self-contained examples organized by category.

For comprehensive real-world CI/CD scenarios, see **[examples/uv-usage-example.md](https://github.com/Nantero1/ai-first-devops-toolkit/blob/main/examples/uv-usage-example.md)**. Some possibilities:

1. 🤖 AI-generated PR review – automated pull request analysis with structured review findings
2. 📝 Commit summarizer – convert commit logs into concise release notes
3. 🔍 Vulnerability scanner – map code vulnerabilities to OWASP standards with actionable remediation
4. 🎯 Quality gate enforcer – validate build artifacts against schema-defined quality criteria
5. 🏦 Loan application analyzer – transform free-text loan applications into Basel-III risk-model inputs
6. 💼 Consulting report generator – convert meeting notes into itemized Statement of Work deliverables
7. 🏛️ Legal contract parser – extract clauses and compute risk scores from contract documents
8. 📝 Court opinion digest – summarize judicial opinions into structured precedent and citation graphs
9. 🏥 Patient intake processor – build HL7/FHIR-compliant patient records from free-form intake forms
10. 📈 Earnings call analyzer – convert transcripts into KPI dashboards for financial performance review
11. 🔍 Code-review bot – scan commits and PRs to produce OWASP-mapped vulnerability reports
12. 🎯 Incident post-mortem summarizer – generate structured root cause analysis and corrective action plans
13. 📊 Regulatory compliance reporter – synthesize regulatory texts into structured compliance checklists
14. 💼 Financial audit note handler – convert audit commentary into ledger-ready journal entries
15. 🔍 Vulnerability scanner – map code vulnerabilities to OWASP standards with actionable remediation
16. 🎯 Quality gate enforcer – validate build artifacts against schema-defined quality criteria
17. 🏦 Loan application analyzer – transform free-text loan applications into Basel-III risk-model inputs
18. 💼 Consulting report generator – convert meeting notes into itemized Statement of Work deliverables
19. 🏛️ Legal contract parser – extract clauses and compute risk scores from contract documents
20. 📝 Court opinion digest – summarize judicial opinions into structured precedent and citation graphs
21. 🏥 Patient intake processor – build HL7/FHIR-compliant patient records from free-form intake forms
22. 📈 Earnings call analyzer – convert transcripts into KPI dashboards for financial performance review
23. 🔍 Code-review bot – scan commits and PRs to produce OWASP-mapped vulnerability reports
24. 🎯 Incident post-mortem summarizer – generate structured root cause analysis and corrective action plans
25. 📊 Regulatory compliance reporter – synthesize regulatory texts into structured compliance checklists
26. 💼 Financial audit note handler – convert audit commentary into ledger-ready journal entries
27. 🔧 Technical review assistant – output structured code review reports with clear action items
28. 🏥 Doctor dictation converter – transform verbal notes into ICD-10 coded encounter records
29. 🏛️ Legal discovery summarizer – extract key issues and risks from large document sets
30. 📁 Manufacturing defect analyzer – build 8D corrective-action records from production issue notes
31. 💹 Budget variance analyzer – summarize financial reports into detailed KPI and variance analyses
32. 🖥️ Ticket triage assistant – prioritize technical support tickets with automated incident classification
33. 🏦 Compliance transformer – create structured Basel reports from raw regulatory text
34. 📊 Credit risk evaluator – convert customer feedback into quantifiable risk scores
35. 💰 Investor memo summarizer – distill strategic memos into pitch-deck bullet points
36. 🛡️ Cyber threat mapper – translate security alerts into MITRE ATT&CK mapped incident reports
37. 👷 Equipment maintenance scheduler – analyze sensor logs to generate predictive maintenance reports
38. 🫀 Health history compiler – produce structured patient histories from narrative medical notes
39. 🛑 Safety inspection checker – transform inspection narratives into OSHA citation checklists
40. 🏥 Radiology result formatter – convert radiology reports into SNOMED-coded JSON outputs
41. 📝 Insurance claim analyzer – structure claim narratives into automated claim assessments
42. 💼 Contract review summarizer – extract risk factors and key dates from legal contracts
43. 🔍 Fraud detector – transform analyst notes into SAR (Suspicious Activity Report) JSON objects
44. 🏛️ Policy impact assessor – convert policy proposals into stakeholder impact matrices
45. 🏭 Production incident reporter – build actionable recovery plans from factory incident logs
46. 📝 Documentation updater – generate schema-compliant technical documentation automatically
47. 🔄 API diff analyzer – produce backward-compatibility risk reports from API specification changes
48. 📊 Financial forecaster – summarize financial reports into structured cash-flow and projection objects
49. 🔧 Deployment log analyzer – convert rollout logs into performance and downtime metrics
50. 🛒 E-commerce sentiment analyzer – tag customer reviews with sentiment and key product features
51. 🎙️ Meeting minute extractor – transform recorded meetings into action items and follow-up tasks
52. 📝 Sprint retrospective summarizer – generate improvement plans from agile team discussions
53. 🏥 Clinical trial data packager – automatically structure clinical notes for FDA-submission
54. 🏢 Employee feedback analyzer – convert free-text feedback into HR insights and action checklists
55. 🛠️ Process efficiency reporter – output production logs into structured performance metrics
56. 🏛️ Legal bill auditor – transform billing details into itemized expense and compliance reports
57. 📦 Automated inventory trigger – build reordering reports from warehouse inventory logs
58. 🧾 Receipt processor – convert OCR receipts into ledger-ready accounting entries
59. 🏦 Mortgage eligibility assessor – analyze mortgage applications to generate risk and eligibility scores
60. 🚧 Infrastructure incident analyst – summarize log files into detailed RCAs and incident timelines
61. 🏛️ Regulatory update tracker – generate structured compliance action items from updated guidelines
62. 📝 Board meeting summarizer – extract key decisions and action items from meeting transcripts
63. 🔍 Vulnerability risk assessor – create remediation plans by mapping findings to risk frameworks
64. 💼 Legal email analyzer – extract key issues and deadlines from email threads for legal review
65. 🏥 Prescription manager – transform handwritten prescription notes into structured medication lists
66. 🖥️ Git log analyzer – generate detailed changelogs from version control commit histories
67. 📋 SOP generator – create standard operating procedures with checklist items from process descriptions
68. 🎯 PR triage tool – score and tag pull requests by urgency and impact automatically
69. 🏦 Audit finding summarizer – convert audit observations into structured compliance and risk reports
70. 📈 Market trend analyzer – synthesize marketing data into structured trend forecasting objects
71. 🧑‍💼 Proposal evaluator – produce structured scoring and evaluation criteria from project proposals
72. 🏢 Operations dashboard creator – translate facility logs into productivity and efficiency metrics
73. 🏥 Lab result organizer – build structured diagnostic tables from laboratory results
74. 💡 Innovation evaluator – compile ideation logs into cost-benefit structured analyses
75. 🏛️ Judicial ruling summarizer – generate concise, structured digests from court rulings
76. 🔧 Commit changelog generator – extract impactful changes from commit logs for release summaries
77. 🏭 Production yield analyzer – produce reports on output statistics and downtime from factory logs
78. 💳 Fraud alert generator – transform risk signals into automated CVSS-scored alerts
79. 📝 Regulatory filing assistant – structure raw regulatory data for seamless filing and compliance tracking
80. 👩‍⚕️ Clinical observation compiler – convert medical research notes into structured clinical data entries
81. 🚀 Deployment success reporter – summarize production rollouts with performance metrics and KPIs
82. 🏦 Mortgage risk evaluator – process mortgage files into detailed risk scoring and eligibility summaries
83. 💼 Contract amendment monitor – track version changes and compliance updates in amended contracts
84. 🏥 Vital signs monitor – generate alert reports from patient vital signs and anomaly detection
85. 🔐 IT security auditor – convert access logs into structured audit and compliance reports
86. 🚧 Incident ticket classifier – generate detailed RCA reports and automated ticket categorizations
87. 🏛️ Governance mapper – produce structured mappings of internal policies to regulatory frameworks
88. 🏢 Onboarding compliance checker – convert training logs into automated compliance and checklist trackers
89. 📝 Data breach notifier – build structured breach incident reports with remediation plans
90. 🏦 Teller performance analyzer – transform shift logs into performance and error analysis reports
91. 💼 Contract risk assessor – generate automated legal risk memos from detailed contract reviews
92. 🛠️ Bug report classifier – categorize issue reports by severity and produce remediation plans
93. 🏥 Appointment summarizer – convert appointment notes into structured follow-up recommendations
94. 🔄 Data migration manifest – output ETL mapping details into a structured transformation record
95. 🚀 Post-release analyst – synthesize customer feedback into performance improvement metrics
96. 🏭 Equipment efficiency evaluator – analyze production logs to predict maintenance needs and cost analysis
97. 🕵️ Fraud case reporter – compile investigative notes into structured fraud case summaries
98. 🏛️ Compliance checklist generator – map internal controls to GDPR or other frameworks in structured reports
99. 👨‍💻 Diff summarizer – automatically generate summaries of code differences for peer review
100. 📄 Patent claim comparator – produce novelty and prior art comparison tables from patent texts
101. 🔍 Cyber incident analyzer – structure incident narratives into threat intelligence and remediation guides
102. 🛡️ Security audit mapper – create control maps aligned with NIST frameworks from audit notes
103. 🏦 Portfolio risk analyzer – transform investment notes into performance and risk metric summaries
104. 📊 Stress test reporter – compile financial stress test scenarios into structured risk reports
105. 📝 Meeting action tracker – extract decisions and assign tasks from meeting minutes
106. 🛠️ DevOps runbook creator – produce actionable standard operating procedures from runbook logs
107. 🚚 Supply chain optimizer – generate delay forecasts and automated inventory suggestions from logistics notes
108. ⚙️ Process improvement recommender – convert operational logs into structured efficiency recommendations
109. 👮 Compliance reporter – map internal governance policies to GDPR and similar frameworks
110. 🌐 API performance optimizer – analyze API usage logs to generate optimization and performance metrics
111. 🛠️ Legacy system analyzer – assess legacy code bases and produce migration impact reports
112. 🧩 Unstructured anything → your bespoke schema-validated JSON

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

For complete CI/CD examples, see **[examples/uv-usage-example.md](https://github.com/Nantero1/ai-first-devops-toolkit/blob/main/examples/uv-usage-example.md)**.

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
