# Security Policy

## Supported Versions

The following versions of `sqltools-mcp` are currently being supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 0.1.0   | :white_check_mark: |

## Reporting a Vulnerability

Security is a top priority for this project. If you discover a security vulnerability, please do NOT create a public issue. Instead, please follow these steps:

1. **Email the author**: Send an email to [huangzt@example.com](mailto:huangzt@example.com) with the subject "Security Vulnerability".
2. **Provide Details**: Include as much information as possible, including:
   - Type of vulnerability.
   - Steps to reproduce it.
   - Potential impact.
3. **Response**: We will acknowledge your report within 48 hours and provide a timeline for a fix.

## Security Features

This project implements several security measures:
- **Identifier Quoting**: All database objects (like table names) are properly quoted using double quotes or respective database standards to prevent SQL injection in metadata queries.
- **Risk Assessment**: Tools that perform destructive operations (DROP, TRUNCATE, DELETE) are flagged with the `destructiveHint` to alert AI models and users.
- **Credential Protection**: Passwords are never returned in connection status or logs.
