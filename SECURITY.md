# Security Policy

## Reporting Security Issues

Security is paramount in financial software systems. If you discover a vulnerability or potential security exploit within Bison, please do **NOT** open a public issue.

Instead, please report security vulnerabilities directly to the core maintainers via security email.

## Security Practices

- Passwords are hashed using bcrypt with salt.
- JWT tokens use short-lived access times and secret signature verification.
- Sensitive environment configurations (database credentials, secrets) must never be committed to Git.
