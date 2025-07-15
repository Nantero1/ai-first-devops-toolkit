# Multi-Format Output Showcase

This example demonstrates the **flexible output capabilities** of the LLM CI Runner, showing how the same structured data can be output in different formats: **JSON**, **YAML**, and **direct Markdown**. This showcases the library's ability to adapt output format based on file extension.

## 🌟 **Features Demonstrated**

- **✅ JSON Output**: Structured data in JSON format with metadata wrapper
- **✅ YAML Output**: Human-readable YAML format with proper formatting
- **✅ Direct Markdown**: Clean markdown output without JSON wrapper
- **✅ Format Detection**: Automatic format detection based on file extension
- **✅ Metadata Handling**: Consistent metadata across all output formats
- **✅ Schema Enforcement**: 100% schema compliance in all formats

## 📁 **Files**

- **`input.json`** - API documentation request with structured prompt
- **`schema.json`** - JSON schema defining the expected output structure
- **`README.md`** - This comprehensive documentation

## 🔄 **How It Works**

### **1. Output Format Detection**

The LLM CI Runner automatically detects output format based on file extension:

- **`.json`** → JSON output with metadata wrapper
- **`.yaml`** or **`.yml`** → YAML output with metadata wrapper  
- **`.md`** → Direct markdown text (no wrapper)

### **2. Format-Specific Processing**

**JSON Output:**
```json
{
  "success": true,
  "response": {
    "api_overview": { ... },
    "request_format": { ... }
  },
  "metadata": {
    "runner": "llm_ci_runner.py",
    "timestamp": "2025-01-27T10:30:00Z"
  }
}
```

**YAML Output:**
```yaml
success: true
response:
  api_overview:
    endpoint: "/api/v1/auth/login"
    method: "POST"
    description: "Authenticate user with username/password"
  request_format:
    content_type: "application/json"
    parameters:
      - name: "username"
        type: "string"
        required: true
metadata:
  runner: "llm_ci_runner.py"
  timestamp: "2025-01-27T10:30:00Z"
```

**Markdown Output:**
```markdown
# API Documentation: POST /api/v1/auth/login

## Overview
Authenticate user with username/password credentials.

## Request Format
- **Content-Type:** application/json
- **Parameters:**
  - username (string, required)
  - password (string, required)

## Response Format
...
```

## 🚀 **Usage Examples**

### **1. JSON Output**

```bash
llm-ci-runner \
  --input-file examples/06-output-showcase/multi-format-output/input.json \
  --schema-file examples/06-output-showcase/multi-format-output/schema.json \
  --output-file api-docs.json
```

**Output:** Structured JSON with metadata wrapper

### **2. YAML Output**

```bash
llm-ci-runner \
  --input-file examples/06-output-showcase/multi-format-output/input.json \
  --schema-file examples/06-output-showcase/multi-format-output/schema.json \
  --output-file api-docs.yaml
```

**Output:** Human-readable YAML with proper formatting

### **3. Direct Markdown Output**

```bash
llm-ci-runner \
  --input-file examples/06-output-showcase/multi-format-output/input.json \
  --output-file api-docs.md
```

**Output:** Clean markdown documentation without JSON wrapper (no schema needed)

## 📊 **Schema Validation**

Uses comprehensive JSON schema for structured outputs (JSON/YAML only):

**Note:** Schemas are recommended for JSON and YAML outputs to ensure structured data. For markdown output, omit the schema to get clean, readable documentation.

```json
{
  "type": "object",
  "properties": {
    "api_overview": {
      "type": "object",
      "properties": {
        "endpoint": {"type": "string"},
        "method": {
          "type": "string",
          "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]
        },
        "description": {"type": "string"},
        "authentication": {"type": "string"},
        "rate_limiting": {"type": "string"}
      },
      "required": ["endpoint", "method", "description", "authentication", "rate_limiting"]
    },
    "request_format": {
      "type": "object",
      "properties": {
        "content_type": {"type": "string"},
        "parameters": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": {"type": "string"},
              "type": {"type": "string"},
              "required": {"type": "boolean"},
              "description": {"type": "string"},
              "example": {"type": "string"}
            },
            "required": ["name", "type", "required", "description"]
          }
        },
        "example_request": {"type": "object"}
      },
      "required": ["content_type", "parameters", "example_request"]
    },
    "response_format": {
      "type": "object",
      "properties": {
        "success_response": {
          "type": "object",
          "properties": {
            "status_code": {"type": "integer"},
            "description": {"type": "string"},
            "body": {"type": "object"}
          },
          "required": ["status_code", "description", "body"]
        },
        "error_responses": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "status_code": {"type": "integer"},
              "error_code": {"type": "string"},
              "description": {"type": "string"},
              "body": {"type": "object"}
            },
            "required": ["status_code", "error_code", "description", "body"]
          },
          "minItems": 2,
          "maxItems": 6
        }
      },
      "required": ["success_response", "error_responses"]
    },
    "security_considerations": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "aspect": {"type": "string"},
          "description": {"type": "string"},
          "recommendation": {"type": "string"}
        },
        "required": ["aspect", "description", "recommendation"]
      },
      "minItems": 3,
      "maxItems": 8
    },
    "usage_examples": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "language": {"type": "string"},
          "title": {"type": "string"},
          "code": {"type": "string"},
          "description": {"type": "string"}
        },
        "required": ["language", "title", "code", "description"]
      },
      "minItems": 2,
      "maxItems": 5
    },
    "testing": {
      "type": "object",
      "properties": {
        "test_cases": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": {"type": "string"},
              "description": {"type": "string"},
              "input": {"type": "object"},
              "expected_output": {"type": "object"}
            },
            "required": ["name", "description", "input", "expected_output"]
          },
          "minItems": 3,
          "maxItems": 8
        },
        "curl_examples": {
          "type": "array",
          "items": {"type": "string"},
          "minItems": 2,
          "maxItems": 5
        }
      },
      "required": ["test_cases", "curl_examples"]
    },
    "implementation_notes": {
      "type": "array",
      "items": {"type": "string"},
      "minItems": 3,
      "maxItems": 8
    }
  },
  "required": [
    "api_overview",
    "request_format", 
    "response_format",
    "security_considerations",
    "usage_examples",
    "testing",
    "implementation_notes"
  ]
}
```

## 📋 **Expected Outputs**

### **JSON Output (api-docs.json)**
```json
{
  "success": true,
  "response": {
    "api_overview": {
      "endpoint": "/api/v1/auth/login",
      "method": "POST",
      "description": "Authenticate user with username/password credentials",
      "authentication": "None (this endpoint handles authentication)",
      "rate_limiting": "5 requests per minute per IP address"
    },
    "request_format": {
      "content_type": "application/json",
      "parameters": [
        {
          "name": "username",
          "type": "string",
          "required": true,
          "description": "User's email address or username",
          "example": "user@example.com"
        },
        {
          "name": "password",
          "type": "string",
          "required": true,
          "description": "User's password (minimum 8 characters)",
          "example": "securePassword123"
        }
      ],
      "example_request": {
        "username": "user@example.com",
        "password": "securePassword123"
      }
    },
    "response_format": {
      "success_response": {
        "status_code": 200,
        "description": "Authentication successful",
        "body": {
          "success": true,
          "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
          "refresh_token": "refresh_token_here",
          "expires_in": 3600,
          "user": {
            "id": "user_123",
            "email": "user@example.com",
            "name": "John Doe",
            "role": "user"
          }
        }
      },
      "error_responses": [
        {
          "status_code": 400,
          "error_code": "INVALID_CREDENTIALS",
          "description": "Invalid username or password",
          "body": {
            "success": false,
            "error": "INVALID_CREDENTIALS",
            "message": "Invalid username or password"
          }
        },
        {
          "status_code": 401,
          "error_code": "ACCOUNT_LOCKED",
          "description": "Account temporarily locked due to multiple failed attempts",
          "body": {
            "success": false,
            "error": "ACCOUNT_LOCKED",
            "message": "Account locked for 15 minutes",
            "lockout_remaining": 900
          }
        },
        {
          "status_code": 429,
          "error_code": "RATE_LIMIT_EXCEEDED",
          "description": "Too many requests from this IP",
          "body": {
            "success": false,
            "error": "RATE_LIMIT_EXCEEDED",
            "message": "Rate limit exceeded. Try again in 60 seconds",
            "retry_after": 60
          }
        },
        {
          "status_code": 500,
          "error_code": "INTERNAL_SERVER_ERROR",
          "description": "Internal server error",
          "body": {
            "success": false,
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred"
          }
        }
      ]
    },
    "security_considerations": [
      {
        "aspect": "Password Security",
        "description": "Passwords are transmitted over HTTPS and hashed using bcrypt",
        "recommendation": "Ensure HTTPS is always used and implement password strength requirements"
      },
      {
        "aspect": "Token Security",
        "description": "JWT tokens are signed and have configurable expiration",
        "recommendation": "Use short-lived access tokens and implement token refresh mechanism"
      },
      {
        "aspect": "Rate Limiting",
        "description": "Rate limiting prevents brute force attacks",
        "recommendation": "Monitor rate limit violations and implement progressive delays"
      },
      {
        "aspect": "Input Validation",
        "description": "All inputs are validated and sanitized",
        "recommendation": "Implement comprehensive input validation and sanitization"
      },
      {
        "aspect": "Session Management",
        "description": "Sessions are tracked and can be invalidated",
        "recommendation": "Implement session monitoring and automatic cleanup"
      }
    ],
    "usage_examples": [
      {
        "language": "JavaScript",
        "title": "Fetch API Example",
        "code": "const response = await fetch('/api/v1/auth/login', {\n  method: 'POST',\n  headers: {\n    'Content-Type': 'application/json'\n  },\n  body: JSON.stringify({\n    username: 'user@example.com',\n    password: 'securePassword123'\n  })\n});\n\nconst data = await response.json();\nif (data.success) {\n  localStorage.setItem('token', data.token);\n}",
        "description": "Basic authentication using JavaScript Fetch API"
      },
      {
        "language": "Python",
        "title": "Requests Library Example",
        "code": "import requests\n\nresponse = requests.post(\n    'https://api.example.com/api/v1/auth/login',\n    json={\n        'username': 'user@example.com',\n        'password': 'securePassword123'\n    }\n)\n\ndata = response.json()\nif data['success']:\n    token = data['token']\n    # Store token for subsequent requests",
        "description": "Authentication using Python requests library"
      },
      {
        "language": "cURL",
        "title": "Command Line Example",
        "code": "curl -X POST https://api.example.com/api/v1/auth/login \\\n  -H 'Content-Type: application/json' \\\n  -d '{\n    \"username\": \"user@example.com\",\n    \"password\": \"securePassword123\"\n  }'",
        "description": "Command line authentication using cURL"
      }
    ],
    "testing": {
      "test_cases": [
        {
          "name": "Valid Credentials",
          "description": "Test successful authentication with valid credentials",
          "input": {
            "username": "user@example.com",
            "password": "securePassword123"
          },
          "expected_output": {
            "status_code": 200,
            "success": true,
            "token": "jwt_token_here"
          }
        },
        {
          "name": "Invalid Password",
          "description": "Test authentication failure with wrong password",
          "input": {
            "username": "user@example.com",
            "password": "wrongpassword"
          },
          "expected_output": {
            "status_code": 400,
            "success": false,
            "error": "INVALID_CREDENTIALS"
          }
        },
        {
          "name": "Missing Username",
          "description": "Test validation error when username is missing",
          "input": {
            "password": "securePassword123"
          },
          "expected_output": {
            "status_code": 400,
            "success": false,
            "error": "VALIDATION_ERROR"
          }
        },
        {
          "name": "Rate Limit Test",
          "description": "Test rate limiting after multiple rapid requests",
          "input": {
            "username": "user@example.com",
            "password": "securePassword123"
          },
          "expected_output": {
            "status_code": 429,
            "success": false,
            "error": "RATE_LIMIT_EXCEEDED"
          }
        }
      ],
      "curl_examples": [
        "curl -X POST https://api.example.com/api/v1/auth/login -H 'Content-Type: application/json' -d '{\"username\":\"user@example.com\",\"password\":\"securePassword123\"}'",
        "curl -X POST https://api.example.com/api/v1/auth/login -H 'Content-Type: application/json' -d '{\"username\":\"user@example.com\",\"password\":\"wrongpassword\"}'",
        "curl -X POST https://api.example.com/api/v1/auth/login -H 'Content-Type: application/json' -d '{\"password\":\"securePassword123\"}'"
      ]
    },
    "implementation_notes": [
      "Always use HTTPS in production to protect sensitive data transmission",
      "Implement proper error handling for network failures and timeouts",
      "Store tokens securely and implement automatic token refresh",
      "Add logging for security monitoring and debugging",
      "Consider implementing multi-factor authentication for enhanced security",
      "Monitor authentication metrics for unusual patterns",
      "Implement account lockout after multiple failed attempts",
      "Use environment variables for sensitive configuration values"
    ]
  },
  "metadata": {
    "runner": "llm_ci_runner.py",
    "timestamp": "2025-01-27T10:30:00Z"
  }
}
```

### **YAML Output (api-docs.yaml)**
```yaml
success: true
response:
  api_overview:
    endpoint: "/api/v1/auth/login"
    method: "POST"
    description: "Authenticate user with username/password credentials"
    authentication: "None (this endpoint handles authentication)"
    rate_limiting: "5 requests per minute per IP address"
  request_format:
    content_type: "application/json"
    parameters:
      - name: "username"
        type: "string"
        required: true
        description: "User's email address or username"
        example: "user@example.com"
      - name: "password"
        type: "string"
        required: true
        description: "User's password (minimum 8 characters)"
        example: "securePassword123"
    example_request:
      username: "user@example.com"
      password: "securePassword123"
  response_format:
    success_response:
      status_code: 200
      description: "Authentication successful"
      body:
        success: true
        token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        refresh_token: "refresh_token_here"
        expires_in: 3600
        user:
          id: "user_123"
          email: "user@example.com"
          name: "John Doe"
          role: "user"
    error_responses:
      - status_code: 400
        error_code: "INVALID_CREDENTIALS"
        description: "Invalid username or password"
        body:
          success: false
          error: "INVALID_CREDENTIALS"
          message: "Invalid username or password"
      - status_code: 401
        error_code: "ACCOUNT_LOCKED"
        description: "Account temporarily locked due to multiple failed attempts"
        body:
          success: false
          error: "ACCOUNT_LOCKED"
          message: "Account locked for 15 minutes"
          lockout_remaining: 900
      - status_code: 429
        error_code: "RATE_LIMIT_EXCEEDED"
        description: "Too many requests from this IP"
        body:
          success: false
          error: "RATE_LIMIT_EXCEEDED"
          message: "Rate limit exceeded. Try again in 60 seconds"
          retry_after: 60
      - status_code: 500
        error_code: "INTERNAL_SERVER_ERROR"
        description: "Internal server error"
        body:
          success: false
          error: "INTERNAL_SERVER_ERROR"
          message: "An unexpected error occurred"
  security_considerations:
    - aspect: "Password Security"
      description: "Passwords are transmitted over HTTPS and hashed using bcrypt"
      recommendation: "Ensure HTTPS is always used and implement password strength requirements"
    - aspect: "Token Security"
      description: "JWT tokens are signed and have configurable expiration"
      recommendation: "Use short-lived access tokens and implement token refresh mechanism"
    - aspect: "Rate Limiting"
      description: "Rate limiting prevents brute force attacks"
      recommendation: "Monitor rate limit violations and implement progressive delays"
    - aspect: "Input Validation"
      description: "All inputs are validated and sanitized"
      recommendation: "Implement comprehensive input validation and sanitization"
    - aspect: "Session Management"
      description: "Sessions are tracked and can be invalidated"
      recommendation: "Implement session monitoring and automatic cleanup"
  usage_examples:
    - language: "JavaScript"
      title: "Fetch API Example"
      code: |
        const response = await fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            username: 'user@example.com',
            password: 'securePassword123'
          })
        });

        const data = await response.json();
        if (data.success) {
          localStorage.setItem('token', data.token);
        }
      description: "Basic authentication using JavaScript Fetch API"
    - language: "Python"
      title: "Requests Library Example"
      code: |
        import requests

        response = requests.post(
            'https://api.example.com/api/v1/auth/login',
            json={
                'username': 'user@example.com',
                'password': 'securePassword123'
            }
        )

        data = response.json()
        if data['success']:
            token = data['token']
            # Store token for subsequent requests
      description: "Authentication using Python requests library"
    - language: "cURL"
      title: "Command Line Example"
      code: |
        curl -X POST https://api.example.com/api/v1/auth/login \
          -H 'Content-Type: application/json' \
          -d '{
            "username": "user@example.com",
            "password": "securePassword123"
          }'
      description: "Command line authentication using cURL"
  testing:
    test_cases:
      - name: "Valid Credentials"
        description: "Test successful authentication with valid credentials"
        input:
          username: "user@example.com"
          password: "securePassword123"
        expected_output:
          status_code: 200
          success: true
          token: "jwt_token_here"
      - name: "Invalid Password"
        description: "Test authentication failure with wrong password"
        input:
          username: "user@example.com"
          password: "wrongpassword"
        expected_output:
          status_code: 400
          success: false
          error: "INVALID_CREDENTIALS"
      - name: "Missing Username"
        description: "Test validation error when username is missing"
        input:
          password: "securePassword123"
        expected_output:
          status_code: 400
          success: false
          error: "VALIDATION_ERROR"
      - name: "Rate Limit Test"
        description: "Test rate limiting after multiple rapid requests"
        input:
          username: "user@example.com"
          password: "securePassword123"
        expected_output:
          status_code: 429
          success: false
          error: "RATE_LIMIT_EXCEEDED"
    curl_examples:
      - "curl -X POST https://api.example.com/api/v1/auth/login -H 'Content-Type: application/json' -d '{\"username\":\"user@example.com\",\"password\":\"securePassword123\"}'"
      - "curl -X POST https://api.example.com/api/v1/auth/login -H 'Content-Type: application/json' -d '{\"username\":\"user@example.com\",\"password\":\"wrongpassword\"}'"
      - "curl -X POST https://api.example.com/api/v1/auth/login -H 'Content-Type: application/json' -d '{\"password\":\"securePassword123\"}'"
  implementation_notes:
    - "Always use HTTPS in production to protect sensitive data transmission"
    - "Implement proper error handling for network failures and timeouts"
    - "Store tokens securely and implement automatic token refresh"
    - "Add logging for security monitoring and debugging"
    - "Consider implementing multi-factor authentication for enhanced security"
    - "Monitor authentication metrics for unusual patterns"
    - "Implement account lockout after multiple failed attempts"
    - "Use environment variables for sensitive configuration values"
metadata:
  runner: "llm_ci_runner.py"
  timestamp: "2025-01-27T10:30:00Z"
```

### **Markdown Output (api-docs.md)**
*Note: Markdown output works best WITHOUT a schema to produce clean, readable documentation. With a schema, the output would contain JSON structure.*

```markdown
# API Documentation: POST /api/v1/auth/login

## Overview
Authenticate user with username/password credentials.

**Endpoint:** `/api/v1/auth/login`  
**Method:** `POST`  
**Authentication:** None (this endpoint handles authentication)  
**Rate Limiting:** 5 requests per minute per IP address

## Request Format

**Content-Type:** `application/json`

### Parameters
| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| username | string | Yes | User's email address or username | `user@example.com` |
| password | string | Yes | User's password (minimum 8 characters) | `securePassword123` |

### Example Request
```json
{
  "username": "user@example.com",
  "password": "securePassword123"
}
```

## Response Format

### Success Response (200)
Authentication successful

```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "refresh_token_here",
  "expires_in": 3600,
  "user": {
    "id": "user_123",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user"
  }
}
```

### Error Responses

#### 400 - Invalid Credentials
Invalid username or password

```json
{
  "success": false,
  "error": "INVALID_CREDENTIALS",
  "message": "Invalid username or password"
}
```

#### 401 - Account Locked
Account temporarily locked due to multiple failed attempts

```json
{
  "success": false,
  "error": "ACCOUNT_LOCKED",
  "message": "Account locked for 15 minutes",
  "lockout_remaining": 900
}
```

#### 429 - Rate Limit Exceeded
Too many requests from this IP

```json
{
  "success": false,
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded. Try again in 60 seconds",
  "retry_after": 60
}
```

#### 500 - Internal Server Error
Internal server error

```json
{
  "success": false,
  "error": "INTERNAL_SERVER_ERROR",
  "message": "An unexpected error occurred"
}
```

## Security Considerations

### Password Security
**Description:** Passwords are transmitted over HTTPS and hashed using bcrypt  
**Recommendation:** Ensure HTTPS is always used and implement password strength requirements

### Token Security
**Description:** JWT tokens are signed and have configurable expiration  
**Recommendation:** Use short-lived access tokens and implement token refresh mechanism

### Rate Limiting
**Description:** Rate limiting prevents brute force attacks  
**Recommendation:** Monitor rate limit violations and implement progressive delays

### Input Validation
**Description:** All inputs are validated and sanitized  
**Recommendation:** Implement comprehensive input validation and sanitization

### Session Management
**Description:** Sessions are tracked and can be invalidated  
**Recommendation:** Implement session monitoring and automatic cleanup

## Usage Examples

### JavaScript (Fetch API)
```javascript
const response = await fetch('/api/v1/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'user@example.com',
    password: 'securePassword123'
  })
});

const data = await response.json();
if (data.success) {
  localStorage.setItem('token', data.token);
}
```

### Python (Requests Library)
```python
import requests

response = requests.post(
    'https://api.example.com/api/v1/auth/login',
    json={
        'username': 'user@example.com',
        'password': 'securePassword123'
    }
)

data = response.json()
if data['success']:
    token = data['token']
    # Store token for subsequent requests
```

### cURL (Command Line)
```bash
curl -X POST https://api.example.com/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "user@example.com",
    "password": "securePassword123"
  }'
```

## Testing

### Test Cases

#### Valid Credentials
**Description:** Test successful authentication with valid credentials  
**Input:**
```json
{
  "username": "user@example.com",
  "password": "securePassword123"
}
```
**Expected Output:**
```json
{
  "status_code": 200,
  "success": true,
  "token": "jwt_token_here"
}
```

#### Invalid Password
**Description:** Test authentication failure with wrong password  
**Input:**
```json
{
  "username": "user@example.com",
  "password": "wrongpassword"
}
```
**Expected Output:**
```json
{
  "status_code": 400,
  "success": false,
  "error": "INVALID_CREDENTIALS"
}
```

#### Missing Username
**Description:** Test validation error when username is missing  
**Input:**
```json
{
  "password": "securePassword123"
}
```
**Expected Output:**
```json
{
  "status_code": 400,
  "success": false,
  "error": "VALIDATION_ERROR"
}
```

#### Rate Limit Test
**Description:** Test rate limiting after multiple rapid requests  
**Input:**
```json
{
  "username": "user@example.com",
  "password": "securePassword123"
}
```
**Expected Output:**
```json
{
  "status_code": 429,
  "success": false,
  "error": "RATE_LIMIT_EXCEEDED"
}
```

### cURL Examples
```bash
# Valid authentication
curl -X POST https://api.example.com/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"user@example.com","password":"securePassword123"}'

# Invalid password
curl -X POST https://api.example.com/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"user@example.com","password":"wrongpassword"}'

# Missing username
curl -X POST https://api.example.com/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"password":"securePassword123"}'
```

## Implementation Notes

- Always use HTTPS in production to protect sensitive data transmission
- Implement proper error handling for network failures and timeouts
- Store tokens securely and implement automatic token refresh
- Add logging for security monitoring and debugging
- Consider implementing multi-factor authentication for enhanced security
- Monitor authentication metrics for unusual patterns
- Implement account lockout after multiple failed attempts
- Use environment variables for sensitive configuration values
```

## 💡 **Benefits of Multi-Format Output**

### **🎯 Format Flexibility**
- Choose the most appropriate format for your use case
- JSON for programmatic consumption
- YAML for human-readable configuration
- Markdown for documentation and publishing

### **📊 Consistent Data Structure**
- Same schema validation across all formats
- Consistent metadata and timestamps
- Guaranteed data integrity

### **🔧 Integration Ready**
- JSON output for API integrations
- YAML output for configuration management
- Markdown output for documentation systems

### **📝 Documentation Quality**
- Professional markdown formatting
- Proper code syntax highlighting
- Structured tables and lists

## 🚀 **Use Cases**

- **API Documentation**: Generate comprehensive API docs in multiple formats
- **Configuration Management**: Output configuration in YAML for deployment
- **Technical Writing**: Create markdown documentation for knowledge bases
- **Data Export**: Export structured data for analysis and reporting
- **Integration Testing**: Generate test data in different formats

## 📚 **Learning Path**

1. **Start with Basic Output**: Try `01-basic/sentiment-analysis/` for simple JSON output
2. **Explore Templates**: Check `05-templates/` for dynamic content generation
3. **Master Multi-Format**: This example shows output flexibility
4. **Advanced Features**: Explore other examples for comprehensive capabilities

---

*Ready to explore output flexibility? This example demonstrates how the LLM CI Runner adapts output format based on file extension, providing the right format for every use case.* 