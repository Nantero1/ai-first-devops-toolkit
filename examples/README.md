# AI-First DevOps Examples

This directory contains comprehensive examples demonstrating AI-first DevOps principles and practices. Each example is self-contained with its input, schema, and documentation.

## 📁 Organization

### 01-basic/ - Foundation Examples
Simple examples to get started with the LLM Runner.

- **[simple-chat/](01-basic/simple-chat/)** - Basic text-only LLM interaction
- **[sentiment-analysis/](01-basic/sentiment-analysis/)** - Structured output with schema enforcement

### 02-devops/ - DevOps Automation
Real-world DevOps scenarios with AI-powered automation.

- **[pr-description/](02-devops/pr-description/)** - Automated PR description generation
- **[changelog-generation/](02-devops/changelog-generation/)** - AI-generated changelogs
- **[code-review/](02-devops/code-review/)** - Automated code review with structured findings

### 03-security/ - Security Analysis
AI-powered security analysis and vulnerability detection.

- **[vulnerability-analysis/](03-security/vulnerability-analysis/)** - Security vulnerability detection

### 04-ai-first/ - AI-First Development
Advanced examples inspired by [AI-First DevOps](https://technologyworkroom.blogspot.com/2025/06/building-ai-first-devops.html) principles.

- **[autonomous-development-plan/](04-ai-first/autonomous-development-plan/)** - AI creates comprehensive development plans

### 05-templates/ - Template-Driven Workflows
Dynamic prompt generation using YAML configuration and Handlebars templates.

- **[pr-review-template/](05-templates/pr-review-template/)** - PR review with Handlebars templates and YAML variables
- **[static-example/](05-templates/static-example/)** - Static template without variables (template-vars optional)

## 🚀 Quick Start

Choose an example based on your needs:

```bash
# Basic text interaction
llm-ci-runner \
  --input-file examples/01-basic/simple-chat/input.json \
  --output-file result.json

# Structured output with schema
llm-ci-runner \
  --input-file examples/01-basic/sentiment-analysis/input.json \
  --output-file result.json \
  --schema-file examples/01-basic/sentiment-analysis/schema.json

# AI-First development planning
llm-ci-runner \
  --input-file examples/04-ai-first/autonomous-development-plan/input.json \
  --output-file plan.json \
  --schema-file examples/04-ai-first/autonomous-development-plan/schema.json

# Template-based workflow with YAML
llm-ci-runner \
  --template-file examples/05-templates/pr-review-template/template.hbs \
  --template-vars examples/05-templates/pr-review-template/template-vars.yaml \
  --schema-file examples/05-templates/pr-review-template/schema.yaml \
  --output-file pr-review-result.yaml

# Static template without variables (template-vars optional)
llm-ci-runner \
  --template-file examples/05-templates/static-example/template.hbs \
  --schema-file examples/05-templates/static-example/schema.yaml \
  --output-file code-analysis-result.yaml
```

## 🎯 AI-First DevOps Principles

These examples embody the principles from [Building AI-First DevOps](https://technologyworkroom.blogspot.com/2025/06/building-ai-first-devops.html):

| Traditional Approach | AI-First Approach (These Examples) |
|---------------------|-----------------------------------|
| Manual documentation | 🤖 AI-generated docs with guaranteed consistency |
| Human code reviews | 🤖 AI-powered reviews with structured findings |
| Reactive security | 🔍 Proactive AI security analysis |
| Manual planning | 🎯 AI-driven development planning |
| Linear productivity | 📈 Exponential gains through intelligent automation |

## 📋 Example Structure

Traditional examples follow this structure:
```
example-name/
├── README.md          # Documentation and usage instructions
├── input.json         # LLM prompt and context
├── schema.json        # Structured output schema (if applicable)
└── additional files   # Any other supporting files
```

**Template-based examples** use this structure:
```
template-example/
├── README.md          # Documentation and usage instructions
├── template.hbs       # Handlebars template for dynamic prompts
├── template-vars.yaml # YAML variables to populate the template
├── schema.yaml        # YAML schema for output structure
└── additional files   # Any other supporting files
```

## 🔗 Integration Examples

For comprehensive CI/CD integration examples, see **[uv-usage-example.md](uv-usage-example.md)** which includes:
- GitHub Actions workflows
- Multi-stage AI pipelines
- Quality gates and validation
- Real-world deployment scenarios

## 🎨 Schema Features Demonstrated

- **Enum Constraints**: Predefined value validation
- **Numeric Ranges**: Min/max value enforcement
- **Array Limits**: Min/max item counts
- **String Constraints**: Length and pattern validation
- **Complex Objects**: Nested structure validation
- **Required Fields**: Mandatory field enforcement
- **YAML Schemas**: Define schemas in readable YAML format
- **Template Variables**: Dynamic schema population from variables

## 🚀 Getting Started

1. **Start Simple**: Begin with `01-basic/simple-chat/` for basic usage
2. **Add Structure**: Try `01-basic/sentiment-analysis/` for schema enforcement
3. **DevOps Integration**: Explore `02-devops/` for CI/CD scenarios
4. **Template Workflows**: Try `05-templates/pr-review-template/` for YAML and Handlebars
5. **AI-First Principles**: Dive into `04-ai-first/` for advanced concepts

## 📚 Learning Path

1. **Foundation** → `01-basic/` - Understand basic concepts
2. **DevOps** → `02-devops/` - Learn CI/CD integration
3. **Security** → `03-security/` - Master security automation
4. **Templates** → `05-templates/` - Master dynamic workflows with YAML and Handlebars
5. **AI-First** → `04-ai-first/` - Embrace the future of development

---

*Ready to transform your development workflow? Start with these examples and build your path to AI-First DevOps. Learn more about the revolution in [Building AI-First DevOps](https://technologyworkroom.blogspot.com/2025/06/building-ai-first-devops.html).* 