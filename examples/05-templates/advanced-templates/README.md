# Advanced Templates with Conditional Rendering & Complex Variables

This example demonstrates **advanced Handlebars template features** including conditional rendering, loops, nested templates, and complex variable structures. It showcases the full power of the template system for dynamic prompt generation.

## 🚀 **Quick Start - Try It Now!**

```bash
llm-ci-runner \
  --template-file examples/05-templates/advanced-templates/template.hbs \
  --template-vars examples/05-templates/advanced-templates/template-vars.yaml \
  --schema-file examples/05-templates/advanced-templates/schema.yaml \
  --output-file advanced-analysis.yaml
```

## 🌟 **Features Demonstrated**

- **✅ Conditional Rendering**: `{{#if}}` and `{{#unless}}` blocks for dynamic content
- **✅ Complex Loops**: `{{#each}}` with nested conditions and formatting
- **✅ Nested Objects**: Deep object traversal and property access
- **✅ Template Composition**: Modular template structure with reusable components
- **✅ Advanced Variables**: Complex YAML structures with arrays, objects, and mixed types
- **✅ Dynamic Content**: Context-aware template rendering based on project type

## 📁 **Files**

- **`template.hbs`** - Advanced Handlebars template with conditional rendering and loops
- **`template-vars.yaml`** - Complex YAML variables demonstrating nested structures
- **`schema.yaml`** - Comprehensive YAML schema for structured analysis output
- **`README.md`** - This comprehensive documentation

## 🔄 **How It Works**

### **1. Advanced Template Features**

The template demonstrates sophisticated Handlebars capabilities:

```handlebars
{{#if expertise.certifications}}
**Certifications:** {{#each expertise.certifications}}{{this}}{{#unless @last}}, {{/unless}}{{/each}}
{{/if}}

{{#each project.requirements}}
{{#if this.priority}}
**{{this.priority}} Priority:** {{this.description}}
{{else}}
- {{this.description}}
{{/if}}
{{/each}}
```

### **2. Complex Variable Structures**

Uses nested YAML objects with arrays, conditionals, and mixed data types:

```yaml
expertise:
  role: "Senior Software Architect"
  certifications: ["AWS Solutions Architect Professional", "Google Cloud Professional Cloud Architect"]
  focus_areas: ["Scalability and performance optimization", "Security best practices"]

project:
  requirements:
    - priority: "High"
      description: "Migrate from monolithic to microservices architecture"
    - description: "Improve mobile app performance by 50%"
```

### **3. Dynamic Content Generation**

Template adapts content based on available variables:

- **Conditional sections** appear only when data is present
- **Loops with formatting** handle arrays with proper comma separation
- **Nested conditionals** provide context-aware rendering
- **Complex object traversal** accesses deeply nested properties

## 🚀 **Usage**

### **Primary Command**

```bash
llm-ci-runner \
  --template-file examples/05-templates/advanced-templates/template.hbs \
  --template-vars examples/05-templates/advanced-templates/template-vars.yaml \
  --schema-file examples/05-templates/advanced-templates/schema.yaml \
  --output-file advanced-analysis.yaml
```

### **Alternative: JSON Output**

```bash
llm-ci-runner \
  --template-file examples/05-templates/advanced-templates/template.hbs \
  --template-vars examples/05-templates/advanced-templates/template-vars.yaml \
  --schema-file examples/05-templates/advanced-templates/schema.yaml \
  --output-file advanced-analysis.json
```

## 📊 **Template Variables (template-vars.yaml)**

### **Expertise Section**
```yaml
expertise:
  role: "Senior Software Architect"
  domain: "Cloud-Native Applications & Microservices"
  years_experience: 12
  certifications:
    - "AWS Solutions Architect Professional"
    - "Google Cloud Professional Cloud Architect"
    - "Azure Solutions Architect Expert"
    - "Kubernetes Administrator (CKA)"
  specializations:
    - "Distributed Systems Design"
    - "Performance Optimization"
    - "Security Architecture"
  focus_areas:
    - "Scalability and performance optimization"
    - "Security best practices and compliance"
    - "Code quality and maintainability"
  methodology: "Agile/Scrum with continuous integration and deployment"
```

### **Project Section**
```yaml
project:
  name: "E-Commerce Platform Modernization"
  industry: "Retail & E-Commerce"
  scale: "Enterprise (100K+ daily users)"
  tech_stack:
    - "React.js (Frontend)"
    - "Node.js/Express (Backend)"
    - "PostgreSQL (Primary Database)"
    - "Redis (Caching)"
  team_size: 25
  timeline: "6 months"
  constraints:
    - "Must maintain 99.9% uptime during migration"
    - "Zero-downtime deployment requirements"
    - "PCI DSS compliance for payment processing"
  requirements:
    - priority: "High"
      description: "Migrate from monolithic to microservices architecture"
    - priority: "High"
      description: "Implement real-time inventory management"
    - priority: "Medium"
      description: "Add AI-powered product recommendations"
    - description: "Improve mobile app performance by 50%"
```

### **Analysis Context**
```yaml
analysis:
  type: "comprehensive code review and architecture assessment"
  criteria:
    - "Security vulnerabilities and best practices"
    - "Performance bottlenecks and optimization opportunities"
    - "Scalability concerns and architectural improvements"
  special_instructions: "Focus on actionable recommendations with implementation priorities"

context:
  code_review:
    - "Authentication and authorization mechanisms"
    - "Database query optimization and indexing"
    - "API design and RESTful principles"
  security_audit:
    - "Input validation and sanitization"
    - "SQL injection prevention"
    - "XSS and CSRF protection"
  performance_review:
    - "Database query performance"
    - "API response times"
    - "Frontend bundle size and loading times"
```

## 🎯 **Schema Validation**

Uses comprehensive YAML schema for structured analysis output:

```yaml
type: object
required:
  - summary
  - overall_assessment
  - security_analysis
  - performance_analysis
  - architecture_recommendations
  - implementation_plan
  - risk_assessment
properties:
  summary:
    type: string
    description: "Executive summary of the analysis findings"
    maxLength: 300
  overall_assessment:
    type: object
    properties:
      score:
        type: integer
        minimum: 1
        maximum: 10
      grade:
        type: string
        enum: ["A", "B", "C", "D", "F"]
      strengths:
        type: array
        items:
          type: string
        minItems: 2
        maxItems: 6
      critical_issues:
        type: array
        items:
          type: string
    required: ["score", "grade", "strengths", "critical_issues"]
  security_analysis:
    type: object
    properties:
      vulnerabilities:
        type: array
        items:
          type: object
          properties:
            severity:
              type: string
              enum: ["critical", "high", "medium", "low", "info"]
            category:
              type: string
              enum: ["authentication", "authorization", "data_protection", "input_validation", "session_management", "encryption", "logging", "other"]
            description:
              type: string
              minLength: 20
            location:
              type: string
            remediation:
              type: string
              minLength: 20
            effort:
              type: string
              enum: ["low", "medium", "high"]
          required: ["severity", "category", "description", "remediation"]
        minItems: 1
        maxItems: 10
      compliance_status:
        type: object
        properties:
          pci_dss:
            type: string
            enum: ["compliant", "non_compliant", "partial", "not_applicable"]
          gdpr:
            type: string
            enum: ["compliant", "non_compliant", "partial", "not_applicable"]
          sox:
            type: string
            enum: ["compliant", "non_compliant", "partial", "not_applicable"]
        required: ["pci_dss", "gdpr", "sox"]
    required: ["vulnerabilities", "compliance_status"]
  performance_analysis:
    type: object
    properties:
      bottlenecks:
        type: array
        items:
          type: object
          properties:
            component:
              type: string
            issue:
              type: string
            impact:
              type: string
              enum: ["high", "medium", "low"]
            optimization:
              type: string
          required: ["component", "issue", "impact", "optimization"]
      recommendations:
        type: array
        items:
          type: string
        minItems: 3
        maxItems: 8
    required: ["bottlenecks", "recommendations"]
  architecture_recommendations:
    type: object
    properties:
      patterns:
        type: array
        items:
          type: object
          properties:
            name:
              type: string
            description:
              type: string
            benefit:
              type: string
            implementation_effort:
              type: string
              enum: ["low", "medium", "high"]
          required: ["name", "description", "benefit", "implementation_effort"]
      anti_patterns:
        type: array
        items:
          type: object
          properties:
            name:
              type: string
            description:
              type: string
            risk:
              type: string
            mitigation:
              type: string
          required: ["name", "description", "risk", "mitigation"]
    required: ["patterns", "anti_patterns"]
  implementation_plan:
    type: object
    properties:
      phases:
        type: array
        items:
          type: object
          properties:
            phase:
              type: string
              enum: ["immediate", "short_term", "medium_term", "long_term"]
            duration_weeks:
              type: integer
              minimum: 1
              maximum: 26
            tasks:
              type: array
              items:
                type: object
                properties:
                  task:
                    type: string
                  priority:
                    type: string
                    enum: ["critical", "high", "medium", "low"]
                  effort_days:
                    type: integer
                    minimum: 1
                    maximum: 30
                  dependencies:
                    type: array
                    items:
                      type: string
                required: ["task", "priority", "effort_days"]
          required: ["phase", "duration_weeks", "tasks"]
        minItems: 2
        maxItems: 4
      resource_requirements:
        type: object
        properties:
          developers:
            type: integer
            minimum: 1
          devops_engineers:
            type: integer
            minimum: 0
          security_specialists:
            type: integer
            minimum: 0
          qa_engineers:
            type: integer
            minimum: 0
        required: ["developers"]
    required: ["phases", "resource_requirements"]
  risk_assessment:
    type: object
    properties:
      risks:
        type: array
        items:
          type: object
          properties:
            risk:
              type: string
            probability:
              type: string
              enum: ["low", "medium", "high", "critical"]
            impact:
              type: string
              enum: ["low", "medium", "high", "critical"]
            mitigation:
              type: string
            contingency:
              type: string
          required: ["risk", "probability", "impact", "mitigation"]
      overall_risk_score:
        type: number
        minimum: 1
        maximum: 10
    required: ["risks", "overall_risk_score"]
  technical_debt:
    type: object
    properties:
      total_debt:
        type: string
        enum: ["low", "medium", "high", "critical"]
      categories:
        type: array
        items:
          type: object
          properties:
            category:
              type: string
            debt_level:
              type: string
              enum: ["low", "medium", "high", "critical"]
            description:
              type: string
            impact:
              type: string
          required: ["category", "debt_level", "description", "impact"]
    required: ["total_debt", "categories"]
  monitoring_recommendations:
    type: array
    items:
      type: object
      properties:
        metric:
          type: string
        threshold:
          type: string
        alert_level:
          type: string
          enum: ["info", "warning", "critical"]
        implementation:
          type: string
      required: ["metric", "threshold", "alert_level", "implementation"]
    minItems: 3
    maxItems: 10
additionalProperties: false
```

## 📋 **Expected Output**

The command generates comprehensive structured analysis:

```yaml
success: true
response:
  summary: "The E-Commerce Platform Modernization project shows strong architectural foundations with some critical security vulnerabilities that must be addressed immediately. The migration to microservices is well-planned but requires careful attention to data consistency and monitoring."
  overall_assessment:
    score: 7
    grade: "B"
    strengths:
      - "Well-defined microservices architecture plan"
      - "Strong DevOps practices with CI/CD pipeline"
      - "Comprehensive technology stack selection"
      - "Clear project timeline and resource allocation"
    critical_issues:
      - "SQL injection vulnerability in authentication service"
      - "Missing input validation in payment processing"
      - "Inadequate session management security"
  security_analysis:
    vulnerabilities:
      - severity: "critical"
        category: "input_validation"
        description: "SQL injection vulnerability in user authentication allows unauthorized access"
        location: "src/auth/authentication.js:15"
        remediation: "Replace string concatenation with parameterized queries"
        effort: "low"
      - severity: "high"
        category: "session_management"
        description: "Session tokens lack proper expiration and rotation mechanisms"
        location: "src/auth/session.js:25"
        remediation: "Implement token expiration and automatic rotation"
        effort: "medium"
      - severity: "medium"
        category: "data_protection"
        description: "Sensitive data not encrypted at rest in development environment"
        location: "config/database.js:10"
        remediation: "Enable encryption for all sensitive data storage"
        effort: "high"
    compliance_status:
      pci_dss: "non_compliant"
      gdpr: "partial"
      sox: "compliant"
  performance_analysis:
    bottlenecks:
      - component: "Database Queries"
        issue: "N+1 query problem in product listing"
        impact: "high"
        optimization: "Implement eager loading and query optimization"
      - component: "Frontend Bundle"
        issue: "Large JavaScript bundle size (2.5MB)"
        impact: "medium"
        optimization: "Code splitting and lazy loading implementation"
      - component: "API Response Time"
        issue: "Slow authentication endpoint (800ms average)"
        impact: "medium"
        optimization: "Implement Redis caching for user sessions"
    recommendations:
      - "Implement database connection pooling and query optimization"
      - "Add Redis caching layer for frequently accessed data"
      - "Implement CDN for static assets and API responses"
      - "Optimize frontend bundle with code splitting"
      - "Add performance monitoring and alerting"
      - "Implement database indexing strategy"
      - "Set up automated performance testing in CI/CD"
  architecture_recommendations:
    patterns:
      - name: "Circuit Breaker Pattern"
        description: "Implement circuit breakers for external service calls"
        benefit: "Improves system resilience and prevents cascading failures"
        implementation_effort: "medium"
      - name: "Event Sourcing"
        description: "Use event sourcing for audit trail and data consistency"
        benefit: "Provides complete audit trail and enables temporal queries"
        implementation_effort: "high"
      - name: "CQRS Pattern"
        description: "Separate read and write operations for better scalability"
        benefit: "Optimizes read performance and enables independent scaling"
        implementation_effort: "high"
    anti_patterns:
      - name: "Monolithic Database"
        description: "Single database serving all microservices"
        risk: "Creates tight coupling and scalability bottlenecks"
        mitigation: "Implement database per service pattern"
      - name: "Shared Libraries"
        description: "Common libraries shared across all services"
        risk: "Creates versioning conflicts and deployment dependencies"
        mitigation: "Use API contracts and service mesh for communication"
  implementation_plan:
    phases:
      - phase: "immediate"
        duration_weeks: 2
        tasks:
          - task: "Fix SQL injection vulnerabilities"
            priority: "critical"
            effort_days: 3
            dependencies: []
          - task: "Implement input validation for payment processing"
            priority: "critical"
            effort_days: 5
            dependencies: []
          - task: "Set up security monitoring and alerting"
            priority: "high"
            effort_days: 4
            dependencies: []
      - phase: "short_term"
        duration_weeks: 8
        tasks:
          - task: "Implement Redis caching layer"
            priority: "high"
            effort_days: 10
            dependencies: ["security fixes"]
          - task: "Optimize database queries and add indexes"
            priority: "high"
            effort_days: 8
            dependencies: []
          - task: "Implement circuit breaker pattern"
            priority: "medium"
            effort_days: 12
            dependencies: ["caching layer"]
      - phase: "medium_term"
        duration_weeks: 12
        tasks:
          - task: "Migrate to microservices architecture"
            priority: "high"
            effort_days: 40
            dependencies: ["short term optimizations"]
          - task: "Implement CQRS pattern"
            priority: "medium"
            effort_days: 30
            dependencies: ["microservices migration"]
      - phase: "long_term"
        duration_weeks: 8
        tasks:
          - task: "Implement event sourcing"
            priority: "medium"
            effort_days: 25
            dependencies: ["CQRS implementation"]
          - task: "Add AI-powered recommendations"
            priority: "low"
            effort_days: 20
            dependencies: ["event sourcing"]
    resource_requirements:
      developers: 8
      devops_engineers: 2
      security_specialists: 1
      qa_engineers: 3
  risk_assessment:
    risks:
      - risk: "Data loss during microservices migration"
        probability: "medium"
        impact: "critical"
        mitigation: "Implement comprehensive backup and rollback procedures"
        contingency: "Maintain parallel systems during transition period"
      - risk: "Performance degradation during migration"
        probability: "high"
        impact: "medium"
        mitigation: "Implement gradual migration with feature flags"
        contingency: "Rollback to monolithic system if performance drops"
      - risk: "Security vulnerabilities in new microservices"
        probability: "medium"
        impact: "high"
        mitigation: "Implement security-first development practices"
        contingency: "Regular security audits and penetration testing"
    overall_risk_score: 6.5
  technical_debt:
    total_debt: "medium"
    categories:
      - category: "Code Quality"
        debt_level: "medium"
        description: "Inconsistent coding standards and lack of automated testing"
        impact: "Reduced development velocity and increased bug frequency"
      - category: "Architecture"
        debt_level: "high"
        description: "Monolithic architecture limiting scalability"
        impact: "Difficulty in scaling and maintaining the system"
      - category: "Security"
        debt_level: "critical"
        description: "Multiple security vulnerabilities requiring immediate attention"
        impact: "High risk of data breaches and compliance violations"
      - category: "Performance"
        debt_level: "medium"
        description: "Unoptimized database queries and lack of caching"
        impact: "Poor user experience and high infrastructure costs"
  monitoring_recommendations:
    - metric: "API Response Time"
      threshold: "500ms"
      alert_level: "warning"
      implementation: "Add response time monitoring to all API endpoints"
    - metric: "Database Connection Pool"
      threshold: "80%"
      alert_level: "critical"
      implementation: "Monitor connection pool utilization and scale accordingly"
    - metric: "Error Rate"
      threshold: "1%"
      alert_level: "critical"
      implementation: "Track error rates by endpoint and service"
    - metric: "Cache Hit Rate"
      threshold: "90%"
      alert_level: "warning"
      implementation: "Monitor Redis cache hit rates and optimize caching strategy"
    - metric: "Memory Usage"
      threshold: "85%"
      alert_level: "critical"
      implementation: "Monitor memory usage across all services"
metadata:
  runner: "llm_ci_runner.py"
  timestamp: "2025-01-27T10:30:00Z"
```

## 💡 **Benefits of Advanced Templates**

### **🎯 Dynamic Content Generation**
- Templates adapt to available data
- Conditional sections appear only when relevant
- Complex variable structures enable rich context

### **🔧 Reusable Components**
- Modular template design
- Consistent formatting across different use cases
- Easy maintenance and updates

### **📊 Comprehensive Analysis**
- Structured output with detailed assessments
- Actionable recommendations with effort estimates
- Risk assessment and mitigation strategies

### **🔄 Flexible Configuration**
- YAML variables for easy customization
- Support for complex nested structures
- Conditional rendering based on project type

## 🚀 **Use Cases**

- **Enterprise Architecture Reviews**: Comprehensive system analysis
- **Security Audits**: Detailed vulnerability assessment
- **Performance Optimization**: Bottleneck identification and solutions
- **Compliance Assessments**: Regulatory requirement validation
- **Technical Debt Analysis**: Code quality and architecture evaluation

## 📚 **Learning Path**

1. **Start with Basic Templates**: Try `05-templates/pr-review-template/` first
2. **Explore Advanced Features**: This example shows conditional rendering and loops
3. **Master Complex Variables**: Learn to structure YAML for dynamic templates
4. **Output Flexibility**: Check `06-output-showcase/` for format options

---

*Ready to master advanced template features? This example demonstrates the full power of Handlebars templates with conditional rendering, loops, and complex variable structures.* 