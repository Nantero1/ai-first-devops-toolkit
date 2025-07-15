# Multi-Turn Conversation with Assistant Role Messages

This example demonstrates **multi-turn conversations** with **assistant role messages** and **message names**, showcasing how the LLM CI Runner handles complex conversation flows and maintains context across multiple interactions.

## 🌟 **Features Demonstrated**

- **✅ Assistant Role Messages**: Shows how assistant responses are included in the conversation
- **✅ Message Names**: Demonstrates the optional `name` field for message identification
- **✅ Conversation Flow**: Multi-turn dialogue with context preservation
- **✅ Complex Context**: Rich metadata for conversation tracking
- **✅ Structured Output**: Comprehensive schema for conversation analysis

## 📁 **Files**

- **`input.json`** - Multi-turn conversation with system, user, and assistant messages
- **`schema.json`** - JSON schema defining the expected output structure
- **`README.md`** - This comprehensive documentation

## 🔄 **How It Works**

### **1. Multi-Turn Conversation Structure**

This example demonstrates a realistic conversation flow:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are an expert software architect..."
    },
    {
      "role": "user",
      "content": "I need to design a scalable authentication system...",
      "name": "developer"
    },
    {
      "role": "assistant", 
      "content": "Great! Let me help you design a scalable authentication system..."
    },
    {
      "role": "user",
      "content": "We need to support OAuth2 (Google, GitHub)...",
      "name": "developer"
    },
    {
      "role": "assistant",
      "content": "Perfect! Based on your requirements, here's a comprehensive..."
    },
    {
      "role": "user",
      "content": "Yes, please show me the database schema design...",
      "name": "developer"
    }
  ]
}
```

### **2. Key Features Demonstrated**

**Assistant Role Messages:**
- Assistant responses are included in the conversation history
- Shows how the LLM maintains context across multiple turns
- Demonstrates realistic conversation flow

**Message Names:**
- Optional `name` field identifies message authors
- Useful for tracking conversation participants
- Helps with conversation analysis and debugging

**Rich Context:**
- Session tracking with unique IDs
- Metadata for conversation classification
- Domain-specific context information

## 🚀 **Usage**

### **Primary Command**

```bash
llm-ci-runner \
  --input-file examples/01-basic/multi-turn-conversation/input.json \
  --schema-file examples/01-basic/multi-turn-conversation/schema.json \
  --output-file conversation-result.json
```

### **Alternative: YAML Output**

```bash
llm-ci-runner \
  --input-file examples/01-basic/multi-turn-conversation/input.json \
  --schema-file examples/01-basic/multi-turn-conversation/schema.json \
  --output-file conversation-result.yaml
```

## 📊 **Schema Validation**

Uses comprehensive JSON schema for structured conversation analysis:

```json
{
  "type": "object",
  "properties": {
    "conversation_summary": {
      "type": "string",
      "description": "Summary of the conversation flow and key decisions made",
      "maxLength": 500
    },
    "system_design": {
      "type": "object",
      "properties": {
        "architecture_overview": {
          "type": "string"
        },
        "components": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": {"type": "string"},
              "purpose": {"type": "string"},
              "technology": {"type": "string"},
              "scalability_notes": {"type": "string"}
            },
            "required": ["name", "purpose", "technology"]
          },
          "minItems": 3,
          "maxItems": 10
        },
        "security_features": {
          "type": "array",
          "items": {"type": "string"},
          "minItems": 3,
          "maxItems": 8
        }
      },
      "required": ["architecture_overview", "components", "security_features"]
    },
    "database_schema": {
      "type": "object",
      "properties": {
        "tables": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "table_name": {"type": "string"},
              "columns": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "constraints": {"type": "string"},
                    "description": {"type": "string"}
                  },
                  "required": ["name", "type"]
                }
              },
              "indexes": {
                "type": "array",
                "items": {"type": "string"}
              }
            },
            "required": ["table_name", "columns"]
          },
          "minItems": 2,
          "maxItems": 6
        }
      },
      "required": ["tables"]
    },
    "api_endpoints": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "method": {
            "type": "string",
            "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]
          },
          "endpoint": {"type": "string"},
          "purpose": {"type": "string"},
          "authentication": {
            "type": "string",
            "enum": ["public", "authenticated", "admin"]
          },
          "rate_limiting": {"type": "string"}
        },
        "required": ["method", "endpoint", "purpose", "authentication"]
      },
      "minItems": 5,
      "maxItems": 15
    },
    "implementation_notes": {
      "type": "array",
      "items": {"type": "string"},
      "minItems": 2,
      "maxItems": 8
    },
    "next_steps": {
      "type": "array",
      "items": {"type": "string"},
      "minItems": 2,
      "maxItems": 6
    }
  },
  "required": [
    "conversation_summary",
    "system_design", 
    "database_schema",
    "api_endpoints",
    "implementation_notes",
    "next_steps"
  ]
}
```

## 📋 **Expected Output**

The command generates structured output analyzing the conversation:

```json
{
  "success": true,
  "response": {
    "conversation_summary": "The conversation progressed from initial requirements gathering to detailed system design. The assistant asked clarifying questions about identity providers, session management, and deployment preferences, then provided a comprehensive architecture with security features, database schema, and API endpoints.",
    "system_design": {
      "architecture_overview": "Microservices-based authentication system with API Gateway, Auth Service, User Service, Token Service, PostgreSQL, and Redis for caching and rate limiting.",
      "components": [
        {
          "name": "API Gateway",
          "purpose": "Route authentication requests and handle rate limiting",
          "technology": "AWS API Gateway",
          "scalability_notes": "Auto-scales based on traffic patterns"
        },
        {
          "name": "Auth Service",
          "purpose": "Handle authentication logic and provider integration",
          "technology": "Node.js/Python",
          "scalability_notes": "Stateless design allows horizontal scaling"
        },
        {
          "name": "User Service",
          "purpose": "Manage user data and profile information",
          "technology": "Node.js/Python",
          "scalability_notes": "Read replicas for high availability"
        },
        {
          "name": "Token Service",
          "purpose": "Generate and validate JWT tokens",
          "technology": "Node.js/Python",
          "scalability_notes": "Stateless with Redis for token blacklisting"
        },
        {
          "name": "PostgreSQL",
          "purpose": "Store user data and authentication records",
          "technology": "PostgreSQL",
          "scalability_notes": "Master-slave replication for read scaling"
        },
        {
          "name": "Redis",
          "purpose": "Session caching and rate limiting",
          "technology": "Redis",
          "scalability_notes": "Cluster mode for high availability"
        }
      ],
      "security_features": [
        "JWT tokens with configurable expiration",
        "Rate limiting per IP/user",
        "Input validation and sanitization",
        "Secure password hashing (bcrypt)",
        "HTTPS/TLS encryption",
        "SQL injection prevention",
        "XSS protection",
        "CSRF token validation"
      ]
    },
    "database_schema": {
      "tables": [
        {
          "table_name": "users",
          "columns": [
            {
              "name": "id",
              "type": "UUID",
              "constraints": "PRIMARY KEY",
              "description": "Unique user identifier"
            },
            {
              "name": "email",
              "type": "VARCHAR(255)",
              "constraints": "UNIQUE NOT NULL",
              "description": "User email address"
            },
            {
              "name": "password_hash",
              "type": "VARCHAR(255)",
              "constraints": "NULL",
              "description": "Bcrypt hash for local auth"
            },
            {
              "name": "created_at",
              "type": "TIMESTAMP",
              "constraints": "NOT NULL DEFAULT NOW()",
              "description": "Account creation timestamp"
            },
            {
              "name": "updated_at",
              "type": "TIMESTAMP",
              "constraints": "NOT NULL DEFAULT NOW()",
              "description": "Last update timestamp"
            }
          ],
          "indexes": [
            "CREATE INDEX idx_users_email ON users(email)",
            "CREATE INDEX idx_users_created_at ON users(created_at)"
          ]
        },
        {
          "table_name": "user_providers",
          "columns": [
            {
              "name": "id",
              "type": "UUID",
              "constraints": "PRIMARY KEY",
              "description": "Provider connection identifier"
            },
            {
              "name": "user_id",
              "type": "UUID",
              "constraints": "FOREIGN KEY REFERENCES users(id)",
              "description": "Associated user"
            },
            {
              "name": "provider",
              "type": "VARCHAR(50)",
              "constraints": "NOT NULL",
              "description": "Identity provider (google, github, azure)"
            },
            {
              "name": "provider_user_id",
              "type": "VARCHAR(255)",
              "constraints": "NOT NULL",
              "description": "Provider's user identifier"
            },
            {
              "name": "created_at",
              "type": "TIMESTAMP",
              "constraints": "NOT NULL DEFAULT NOW()",
              "description": "Connection creation timestamp"
            }
          ],
          "indexes": [
            "CREATE UNIQUE INDEX idx_user_providers_unique ON user_providers(user_id, provider)",
            "CREATE INDEX idx_user_providers_provider ON user_providers(provider, provider_user_id)"
          ]
        },
        {
          "table_name": "sessions",
          "columns": [
            {
              "name": "id",
              "type": "UUID",
              "constraints": "PRIMARY KEY",
              "description": "Session identifier"
            },
            {
              "name": "user_id",
              "type": "UUID",
              "constraints": "FOREIGN KEY REFERENCES users(id)",
              "description": "Associated user"
            },
            {
              "name": "token_hash",
              "type": "VARCHAR(255)",
              "constraints": "NOT NULL",
              "description": "Hashed JWT token"
            },
            {
              "name": "expires_at",
              "type": "TIMESTAMP",
              "constraints": "NOT NULL",
              "description": "Token expiration timestamp"
            },
            {
              "name": "created_at",
              "type": "TIMESTAMP",
              "constraints": "NOT NULL DEFAULT NOW()",
              "description": "Session creation timestamp"
            }
          ],
          "indexes": [
            "CREATE INDEX idx_sessions_user_id ON sessions(user_id)",
            "CREATE INDEX idx_sessions_expires_at ON sessions(expires_at)"
          ]
        }
      ]
    },
    "api_endpoints": [
      {
        "method": "POST",
        "endpoint": "/auth/login",
        "purpose": "Authenticate user with username/password",
        "authentication": "public",
        "rate_limiting": "5 requests per minute per IP"
      },
      {
        "method": "POST",
        "endpoint": "/auth/oauth/{provider}",
        "purpose": "Initiate OAuth2 flow with specified provider",
        "authentication": "public",
        "rate_limiting": "10 requests per minute per IP"
      },
      {
        "method": "GET",
        "endpoint": "/auth/oauth/{provider}/callback",
        "purpose": "Handle OAuth2 callback and create session",
        "authentication": "public",
        "rate_limiting": "10 requests per minute per IP"
      },
      {
        "method": "POST",
        "endpoint": "/auth/saml/{provider}",
        "purpose": "Initiate SAML authentication flow",
        "authentication": "public",
        "rate_limiting": "5 requests per minute per IP"
      },
      {
        "method": "POST",
        "endpoint": "/auth/saml/{provider}/callback",
        "purpose": "Handle SAML callback and create session",
        "authentication": "public",
        "rate_limiting": "5 requests per minute per IP"
      },
      {
        "method": "POST",
        "endpoint": "/auth/logout",
        "purpose": "Invalidate current session",
        "authentication": "authenticated",
        "rate_limiting": "10 requests per minute per user"
      },
      {
        "method": "GET",
        "endpoint": "/auth/me",
        "purpose": "Get current user profile",
        "authentication": "authenticated",
        "rate_limiting": "30 requests per minute per user"
      },
      {
        "method": "POST",
        "endpoint": "/auth/refresh",
        "purpose": "Refresh JWT token",
        "authentication": "authenticated",
        "rate_limiting": "20 requests per minute per user"
      },
      {
        "method": "POST",
        "endpoint": "/users",
        "purpose": "Create new user account",
        "authentication": "public",
        "rate_limiting": "3 requests per minute per IP"
      },
      {
        "method": "PUT",
        "endpoint": "/users/{id}",
        "purpose": "Update user profile",
        "authentication": "authenticated",
        "rate_limiting": "10 requests per minute per user"
      },
      {
        "method": "DELETE",
        "endpoint": "/users/{id}",
        "purpose": "Delete user account",
        "authentication": "authenticated",
        "rate_limiting": "1 request per hour per user"
      }
    ],
    "implementation_notes": [
      "Use environment variables for all sensitive configuration",
      "Implement comprehensive logging for security auditing",
      "Set up monitoring and alerting for authentication failures",
      "Use connection pooling for database connections",
      "Implement circuit breakers for external provider calls",
      "Set up automated backups for user data",
      "Configure proper CORS policies for web clients",
      "Implement proper error handling and user feedback"
    ],
    "next_steps": [
      "Set up development environment with Docker Compose",
      "Implement core authentication service with basic endpoints",
      "Add OAuth2 integration for Google and GitHub",
      "Configure SAML integration with Azure AD",
      "Set up PostgreSQL database with proper indexes",
      "Implement Redis caching for session management"
    ]
  },
  "metadata": {
    "runner": "llm_ci_runner.py",
    "timestamp": "2025-01-27T10:30:00Z"
  }
}
```

## 💡 **Benefits of Multi-Turn Conversations**

### **🎯 Context Preservation**
- Assistant responses maintain conversation context
- Complex discussions can span multiple turns
- Rich context metadata for conversation tracking

### **🔍 Message Analysis**
- Track conversation flow and decision points
- Analyze assistant response patterns
- Identify key requirements and solutions

### **📊 Structured Output**
- Comprehensive schema for conversation analysis
- Extract key decisions and design elements
- Generate actionable implementation plans

### **🔄 Realistic Interactions**
- Demonstrates natural conversation flow
- Shows how LLMs handle complex requirements
- Illustrates iterative problem-solving approach

## 🚀 **Use Cases**

- **System Design Sessions**: Multi-turn architecture discussions
- **Requirements Gathering**: Iterative requirement clarification
- **Code Review Conversations**: Back-and-forth code analysis
- **Troubleshooting Sessions**: Step-by-step problem resolution
- **Learning Interactions**: Educational conversations with context

## 📚 **Learning Path**

1. **Start Here**: Understand multi-turn conversation capabilities
2. **Try Templates**: Explore `05-templates/` for dynamic conversations
3. **Advanced Features**: Check `06-output-showcase/` for output flexibility

---

*Ready to explore complex conversation flows? This example demonstrates how the LLM CI Runner handles multi-turn interactions with rich context and structured output.* 