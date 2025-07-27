*This scratchpad file serves as a phase-specific task tracker and implementation guide.*

`MODE SYSTEM TYPES (DO NOT DELETE!):
1. Implementation Type (New Features):
   - Trigger: User requests new implementation
   - Format: MODE: Implementation, FOCUS: New functionality
   - Requirements: Detailed planning, architecture review, documentation
   - Process: Plan mode (🎯) → 95% confidence → Agent mode (⚡)

2. Bug Fix Type (Issue Resolution):
   - Trigger: User reports bug/issue
   - Format: MODE: Bug Fix, FOCUS: Issue resolution
   - Requirements: Problem diagnosis, root cause analysis, solution verification
   - Process: Plan mode (🎯) → Chain of thought analysis → Agent mode (⚡)

Cross-reference with .cursor/memories.md and .cursor/rules/lessons-learned.mdc for context and best practices.`

# Mode: PLAN MODE (🎯)

---

## PLAN MODE: Examples Folder Overhaul for Template-Centric CLI & Library Usage

### 1. Current State Analysis

- **Existing Structure:**
  - Folders like `01-basic`, `02-devops`, `03-security`, etc.
  - Each contains a mix of input files, templates (YAML, Jinja2, Handlebars), and sometimes schema or output files.
  - Naming conventions and structure are inconsistent.
  - Some examples are message-based, some are template-based, but template usage is not the main focus.

- **Codebase Capabilities (from context & scratchpad):**
  - **Template-first:** Supports YAML (Semantic Kernel), Jinja2, Handlebars (hbs), and message-based formats.
  - **Dynamic Model Selection:** YAML templates can specify model_id for Azure OpenAI.
  - **CLI & Library Usage:** Both are supported for running templates, passing variables, and getting outputs.
  - **Schema Validation:** Some examples include schema files for output validation.
  - **Flexible Input:** Can run with input JSON, YAML, or direct message payloads.

---

### 2. New Examples Folder Structure Proposal

#### Top-Level Structure

```
examples/
  README.md
  <usecase-folder>/
    input.json
    template.yaml
    template.j2
    template.hbs
    schema.json
    output.json
    run.sh
    run.py
```

- **Each use case folder** is focused on a real-world scenario (e.g., sentiment analysis, code review, PR feedback).
- **Fixed filenames** in every folder for consistency:
  - `input.json` — Example input variables
  - `template.yaml` — Semantic Kernel YAML template
  - `template.j2` — Jinja2 template
  - `template.hbs` — Handlebars template
  - `schema.json` — Output schema for validation
  - `output.json` — Example output/result
  - `run.sh` — CLI usage example
  - `run.py` — Library usage example

---

#### Proposed Use Case Folders

1. **sentiment-analysis/**
   - Text sentiment classification using all template formats.
   - Shows CLI and library usage for each format.

2. **code-review/**
   - Automated code review comments generation.
   - Includes templates for YAML, Jinja2, Handlebars.
   - Schema for expected output structure.

3. **pr-feedback/**
   - Pull request feedback generation.
   - Demonstrates template-driven feedback with variable injection.

4. **devops-alerts/**
   - DevOps incident or alert message generation.
   - Message-based and template-based examples.

5. **security-audit/**
   - Security audit report generation.
   - Template-driven, with schema validation.

6. **basic-chat/**
   - Simple chat completion (message-based and template-based).

7. **custom-model-selection/**
   - Example showing YAML template with custom model_id for Azure OpenAI.

---

#### Folder Example: sentiment-analysis/

```
sentiment-analysis/
  input.json         # {"text": "I love this product!"}
  template.yaml      # Semantic Kernel YAML template
  template.j2        # Jinja2 template
  template.hbs       # Handlebars template
  schema.json        # Output schema for validation
  output.json        # Example output
  run.sh             # CLI usage: how to run each template
  run.py             # Library usage: how to run each template
```

---

### 3. CLI & Library Usage Examples

- **run.sh**:  
  - Shows how to run each template format via CLI.
  - Example:
    ```sh
    # Run YAML template
    llm-ci-runner --template-file template.yaml --input-file input.json --output-file output.json

    # Run Jinja2 template
    llm-ci-runner --template-file template.j2 --input-file input.json --output-file output.json

    # Run Handlebars template
    llm-ci-runner --template-file template.hbs --input-file input.json --output-file output.json
    ```

- **run.py**:  
  - Shows how to run each template format via library API.
  - Example:
    ```python
    from llm_ci_runner import run_template

    # Run YAML template
    result = run_template("template.yaml", "input.json")
    print(result)

    # Run Jinja2 template
    result = run_template("template.j2", "input.json")
    print(result)

    # Run Handlebars template
    result = run_template("template.hbs", "input.json")
    print(result)
    ```

---

### 4. Message-Based Examples

- Include a `message-based/` folder for direct prompt/message completions (no template).
- Example files:
  - `input.json` — Message payload
  - `run.sh` — CLI usage for message-based completion
  - `run.py` — Library usage for message-based completion

---

### 5. README.md Updates

- At the top level and in each use case folder:
  - Explain the scenario, available templates, and how to run them via CLI and library.
  - Document expected input/output and schema validation.

---

### 6. Summary Table

| Folder                | Purpose                        | Templates         | CLI & Lib Usage | Schema | Output |
|-----------------------|-------------------------------|-------------------|-----------------|--------|--------|
| sentiment-analysis    | Sentiment classification      | yaml, j2, hbs     | Yes             | Yes    | Yes    |
| code-review           | Automated code review         | yaml, j2, hbs     | Yes             | Yes    | Yes    |
| pr-feedback           | PR feedback generation        | yaml, j2, hbs     | Yes             | Yes    | Yes    |
| devops-alerts         | DevOps alert messages         | yaml, j2, hbs     | Yes             | Yes    | Yes    |
| security-audit        | Security audit reports        | yaml, j2, hbs     | Yes             | Yes    | Yes    |
| basic-chat            | Simple chat completion        | yaml, j2, hbs     | Yes             | Yes    | Yes    |
| custom-model-selection| Model selection via YAML      | yaml              | Yes             | Yes    | Yes    |
| message-based         | Direct message completion     | none              | Yes             | No     | Yes    |

---

### 7. Next Steps

- **Design folder skeletons and README.md for each use case.**
- **Draft example templates for each format.**
- **Write CLI and library usage scripts for each folder.**
- **Ensure all filenames are consistent across folders.**
- **Document input/output/schema for each example.**

---

---

## PLAN MODE: Current Examples Use Case Analysis & Preservation Strategy

### Current Use Cases in `examples/` Folder

**01-basic/**
- simple-chat: Basic text-only LLM interaction (free-form output, message-based).
- sentiment-analysis: Structured output with schema enforcement (message-based, schema validation).
- multi-turn-conversation: Multi-turn assistant/user/system message flows, with context and message names.

**02-devops/**
- pr-description: Automated PR description generation (structured output, schema, YAML/JSON input).
- code-review: Automated code review with structured findings and quality gates.
- changelog-generation: AI-generated changelogs.

**03-security/**
- vulnerability-analysis: Security vulnerability detection with structured findings.

**04-ai-first/**
- autonomous-development-plan: AI creates comprehensive development plans for features/projects.

**05-templates/**
- pr-review-template: PR review using Handlebars templates and YAML variables (Semantic Kernel compatible).
- sem-ker-structured-analysis: SK YAML template with embedded schema for structured output.
- sem-ker-simple-question: SK YAML template for simple Q&A with variable substitution.
- release-notes, static-example, advanced-templates, jinja2-example: Various template-driven workflows.

**06-output-showcase/**
- multi-format-output: Demonstrates output in JSON, YAML, Markdown.

---

### How to Preserve Use Cases with Technical Usage Options

For each use case folder (e.g., `sentiment-analysis/`):
- Keep the core scenario and input data.
- Provide 1-2 technical usage options (not all possible options) that best fit the scenario:
  - Message-based (input.json, schema.json)
  - Template-based (template.yaml, template.j2, template.hbs, template-vars.yaml)
  - CLI and/or library usage scripts (run.sh, run.py)
- Document which technical option is recommended for the scenario.

---

#### Example: sentiment-analysis/

```
sentiment-analysis/
  input.json         # Message-based input for CLI/lib
  template.yaml      # SK YAML template for structured output (optional, if relevant)
  schema.json        # Output schema for validation
  output.json        # Example output
  run.sh             # CLI usage for message-based and/or template-based
  run.py             # Library usage for message-based and/or template-based
  README.md          # Explains scenario, technical options, and recommended usage
```

README.md Example Section:
```markdown
## Usage Options

- **Message-based (recommended):**
  - Use `input.json` and `schema.json` for CLI or library.
  - Command: `llm-ci-runner --input-file input.json --schema-file schema.json --output-file output.json`

- **Template-based (advanced):**
  - Use `template.yaml` for SK YAML template workflow.
  - Command: `llm-ci-runner --template-file template.yaml --template-vars input.json --output-file output.json`
```

---

### Summary Table of Use Cases and Technical Options

| Use Case                    | Message-based | Template-based | CLI Usage | Library Usage | Schema |
|-----------------------------|:-------------:|:--------------:|:---------:|:-------------:|:------:|
| simple-chat                 |      ✅       |      ❌        |    ✅     |      ✅       |   ❌   |
| sentiment-analysis          |      ✅       |     (✅)       |    ✅     |      ✅       |   ✅   |
| multi-turn-conversation     |      ✅       |      ❌        |    ✅     |      ✅       |   ✅   |
| pr-description              |      ✅       |     (✅)       |    ✅     |      ✅       |   ✅   |
| code-review                 |      ✅       |     (✅)       |    ✅     |      ✅       |   ✅   |
| vulnerability-analysis      |      ✅       |      ❌        |    ✅     |      ✅       |   ✅   |
| autonomous-dev-plan         |      ✅       |      ❌        |    ✅     |      ✅       |   ✅   |
| pr-review-template          |      ❌       |      ✅        |    ✅     |      ✅       |   ✅   |
| sem-ker-structured-analysis |      ❌       |      ✅        |    ✅     |      ✅       |   ✅   |
| sem-ker-simple-question          |      ❌       |      ✅        |    ✅     |      ✅       |   ❌   |

---

### Key Principle

- Preserve the scenario and input for each use case.
- Provide 1-2 technical usage options per use case, not all possible options.
- Document which option is recommended for clarity.

---

#### What You Mean (Example):

> For `sentiment-analysis`, keep the original message-based example, but also add a template-based option (SK YAML) if it fits. In the README, explain both, but recommend the message-based for most users. Do not add every possible template format to every use case—only those that make sense for the scenario.

---

**Ready to append this analysis and example to the scratchpad for implementation planning.**

---

## PLAN MODE: Proposed New Examples Folder Structure (Use Case Driven)

### Principles
- Each folder = one use case (real-world scenario)
- Only include template formats that make sense for the scenario
- Always provide CLI and library usage scripts
- Schema files only where output is structured
- README in every folder, with scenario, usage, and recommended options

### Proposed Use Case Folders & Templates

#### 1. sentiment-analysis/
*Purpose*: Classify text sentiment, structured output
*Templates*: SK YAML, Jinja2, Handlebars

```
sentiment-analysis/
  input.json
  template.yaml
  template.j2
  template.hbs
  schema.json
  output.json
  run.sh
  run.py
  README.md
```

#### 2. code-review/
*Purpose*: Automated code review, findings, quality gates
*Templates*: SK YAML, Jinja2, Handlebars

```
code-review/
  input.json
  template.yaml
  template.j2
  template.hbs
  schema.json
  output.json
  run.sh
  run.py
  README.md
```

#### 3. pr-description/
*Purpose*: Generate PR descriptions for CI/CD
*Templates*: SK YAML, Jinja2

```
pr-description/
  input.json
  template.yaml
  template.j2
  schema.json
  output.json
  run.sh
  run.py
  README.md
```

#### 4. vulnerability-analysis/
*Purpose*: Security vulnerability detection
*Templates*: SK YAML, Jinja2

```
vulnerability-analysis/
  input.json
  template.yaml
  template.j2
  schema.json
  output.json
  run.sh
  run.py
  README.md
```

#### 5. autonomous-development-plan/
*Purpose*: AI-generated development plans
*Templates*: SK YAML

```
autonomous-development-plan/
  input.json
  template.yaml
  schema.json
  output.json
  run.sh
  run.py
  README.md
```

#### 6. basic-chat/
*Purpose*: Simple chat completion, free-form output
*Templates*: Jinja2, Handlebars

```
basic-chat/
  input.json
  template.j2
  template.hbs
  output.json
  run.sh
  run.py
  README.md
```

#### 7. pr-review-template/
*Purpose*: PR review with SK-compatible Handlebars
*Templates*: Handlebars, YAML vars

```
pr-review-template/
  input.json
  template.hbs
  template-vars.yaml
  schema.yaml
  output.json
  run.sh
  run.py
  README.md
```

#### 8. sem-ker-structured-analysis/
*Purpose*: Structured analysis with embedded schema
*Templates*: SK YAML

```
sem-ker-structured-analysis/
  template.yaml
  template-vars.yaml
  output.json
  run.sh
  run.py
  README.md
```

#### 9. sem-ker-simple-question/
*Purpose*: Simple Q&A with variable substitution
*Templates*: SK YAML

```
sem-ker-simple-question/
  template.yaml
  template-vars.yaml
  output.json
  run.sh
  run.py
  README.md
```

#### 10. multi-format-output/
*Purpose*: Output format comparison (JSON, YAML, Markdown)
*Templates*: Jinja2, Handlebars

```
multi-format-output/
  input.json
  template.j2
  template.hbs
  output.json
  output.yaml
  output.md
  run.sh
  run.py
  README.md
```

#### 11. devops-alerts/
*Purpose*: DevOps incident/alert message generation
*Templates*: Jinja2, Handlebars

```
devops-alerts/
  input.json
  template.j2
  template.hbs
  output.json
  run.sh
  run.py
  README.md
```

#### 12. changelog-generation/
*Purpose*: Automated changelog creation
*Templates*: Jinja2

```
changelog-generation/
  input.json
  template.j2
  output.json
  run.sh
  run.py
  README.md
```

#### 13. custom-model-selection/
*Purpose*: Demonstrate YAML model_id selection for Azure OpenAI
*Templates*: SK YAML

```
custom-model-selection/
  input.json
  template.yaml
  output.json
  run.sh
  run.py
  README.md
```

#### 14. message-based/
*Purpose*: Direct message completion (no template)

```
message-based/
  input.json
  output.json
  run.sh
  run.py
  README.md
```

#### 15. security-audit/
*Purpose*: Security audit report generation
*Templates*: SK YAML, Jinja2

```
security-audit/
  input.json
  template.yaml
  template.j2
  schema.json
  output.json
  run.sh
  run.py
  README.md
```

---

**This folder structure is use case driven, with only relevant template formats per scenario, and every folder includes CLI/lib usage and documentation.**

---

## PLAN MODE: Refined Examples Folder Structure (Complexity-Ordered)

### Principles
- Each folder name starts with a two-digit number (01, 02, ...) indicating complexity (lower = easier)
- Users can learn step-by-step from simple to advanced scenarios
- Table maps each folder to supported formats and usage options

### Refined Use Case Folders (Complexity Ordered)

#### 01-basic-chat/
*Purpose*: Simple chat completion, free-form output
*Templates*: Jinja2, Handlebars
```
01-basic-chat/
  input.json
  template.j2
  template.hbs
  output.json
  run.sh
  run.py
  README.md
```

#### 02-sentiment-analysis/
*Purpose*: Classify text sentiment, structured output
*Templates*: SK YAML, Jinja2, Handlebars
```
02-sentiment-analysis/
  input.json
  template.yaml
  template.j2
  template.hbs
  schema.json
  output.json
  run.sh
  run.py
  README.md
```

#### 03-message-based/
*Purpose*: Direct message completion (no template)
```
03-message-based/
  input.json
  output.json
  run.sh
  run.py
  README.md
```

#### 04-multi-turn-conversation/
*Purpose*: Multi-turn assistant/user/system message flows
*Templates*: Jinja2
```
04-multi-turn-conversation/
  input.json
  template.j2
  output.json
  run.sh
  run.py
  README.md
```

#### 05-devops-alerts/
*Purpose*: DevOps incident/alert message generation
*Templates*: Jinja2, Handlebars
```
05-devops-alerts/
  input.json
  template.j2
  template.hbs
  output.json
  run.sh
  run.py
  README.md
```

#### 06-code-review/
*Purpose*: Automated code review, findings, quality gates
*Templates*: SK YAML, Jinja2, Handlebars
```
06-code-review/
  input.json
  template.yaml
  template.j2
  template.hbs
  schema.json
  output.json
  run.sh
  run.py
  README.md
```

#### 07-pr-description/
*Purpose*: Generate PR descriptions for CI/CD
*Templates*: SK YAML, Jinja2
```
07-pr-description/
  input.json
  template.yaml
  template.j2
  schema.json
  output.json
  run.sh
  run.py
  README.md
```

#### 08-vulnerability-analysis/
*Purpose*: Security vulnerability detection
*Templates*: SK YAML, Jinja2
```
08-vulnerability-analysis/
  input.json
  template.yaml
  template.j2
  schema.json
  output.json
  run.sh
  run.py
  README.md
```

#### 09-security-audit/
*Purpose*: Security audit report generation
*Templates*: SK YAML, Jinja2
```
09-security-audit/
  input.json
  template.yaml
  template.j2
  schema.json
  output.json
  run.sh
  run.py
  README.md
```

#### 10-changelog-generation/
*Purpose*: Automated changelog creation
*Templates*: Jinja2
```
10-changelog-generation/
  input.json
  template.j2
  output.json
  run.sh
  run.py
  README.md
```

#### 11-autonomous-development-plan/
*Purpose*: AI-generated development plans
*Templates*: SK YAML
```
11-autonomous-development-plan/
  input.json
  template.yaml
  schema.json
  output.json
  run.sh
  run.py
  README.md
```

#### 12-custom-model-selection/
*Purpose*: Demonstrate YAML model_id selection for Azure OpenAI
*Templates*: SK YAML
```
12-custom-model-selection/
  input.json
  template.yaml
  output.json
  run.sh
  run.py
  README.md
```

#### 13-pr-review-template/
*Purpose*: PR review with SK-compatible Handlebars
*Templates*: Handlebars, YAML vars
```
13-pr-review-template/
  input.json
  template.hbs
  template-vars.yaml
  schema.yaml
  output.json
  run.sh
  run.py
  README.md
```

#### 14-sem-ker-structured-analysis/
*Purpose*: Structured analysis with embedded schema
*Templates*: SK YAML
```
14-sem-ker-structured-analysis/
  template.yaml
  template-vars.yaml
  output.json
  run.sh
  run.py
  README.md
```

#### 15-sem-ker-simple-question/
*Purpose*: Simple Q&A with variable substitution
*Templates*: SK YAML
```
15-sem-ker-simple-question/
  template.yaml
  template-vars.yaml
  output.json
  run.sh
  run.py
  README.md
```

#### 16-multi-format-output/
*Purpose*: Output format comparison (JSON, YAML, Markdown)
*Templates*: Jinja2, Handlebars
```
16-multi-format-output/
  input.json
  template.j2
  template.hbs
  output.json
  output.yaml
  output.md
  run.sh
  run.py
  README.md
```

---

### Table: Folder, Formats, Usage Options

| Folder                      | Templates         | Message-based | SK YAML | Jinja2 | Handlebars | CLI Usage | Lib Usage | Schema |
|-----------------------------|-------------------|:-------------:|:-------:|:------:|:----------:|:---------:|:---------:|:------:|
| 01-basic-chat               | j2, hbs           |      ✅       |   ❌    |   ✅   |     ✅     |    ✅     |    ✅     |   ❌   |
| 02-sentiment-analysis       | yaml, j2, hbs     |      ✅       |   ✅    |   ✅   |     ✅     |    ✅     |    ✅     |   ✅   |
| 03-message-based            | none              |      ✅       |   ❌    |   ❌   |     ❌     |    ✅     |    ✅     |   ❌   |
| 04-multi-turn-conversation  | j2                |      ✅       |   ❌    |   ✅   |     ❌     |    ✅     |    ✅     |   ✅   |
| 05-devops-alerts            | j2, hbs           |      ✅       |   ❌    |   ✅   |     ✅     |    ✅     |    ✅     |   ❌   |
| 06-code-review              | yaml, j2, hbs     |      ✅       |   ✅    |   ✅   |     ✅     |    ✅     |    ✅     |   ✅   |
| 07-pr-description           | yaml, j2          |      ✅       |   ✅    |   ✅   |     ❌     |    ✅     |    ✅     |   ✅   |
| 08-vulnerability-analysis   | yaml, j2          |      ✅       |   ✅    |   ✅   |     ❌     |    ✅     |    ✅     |   ✅   |
| 09-security-audit           | yaml, j2          |      ✅       |   ✅    |   ✅   |     ❌     |    ✅     |    ✅     |   ✅   |
| 10-changelog-generation     | j2                |      ✅       |   ❌    |   ✅   |     ❌     |    ✅     |    ✅     |   ❌   |
| 11-autonomous-development-plan | yaml           |      ✅       |   ✅    |   ❌   |     ❌     |    ✅     |    ✅     |   ✅   |
| 12-custom-model-selection   | yaml              |      ✅       |   ✅    |   ❌   |     ❌     |    ✅     |    ✅     |   ❌   |
| 13-pr-review-template       | hbs, yaml-vars    |      ❌       |   ❌    |   ❌   |     ✅     |    ✅     |    ✅     |   ✅   |
| 14-sem-ker-structured-analysis   | yaml              |      ❌       |   ✅    |   ❌   |     ❌     |    ✅     |    ✅     |   ❌   |
| 15-sem-ker-simple-question       | yaml              |      ❌       |   ✅    |   ❌   |     ❌     |    ✅     |    ✅     |   ❌   |
| 16-multi-format-output      | j2, hbs           |      ✅       |   ❌    |   ✅   |     ✅     |    ✅     |    ✅     |   ❌   |

---

**This refined structure enables progressive learning from easy to complex, with clear mapping of formats and usage options per example.**