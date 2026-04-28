# Agent Rules

## Brief Description

This repository is a FastAPI prototype for a restaurant recommendation workflow. It currently collects survey answers via an HTML form and persists state to `estado.json`. Recommendation logic and external integrations are not implemented yet.

## Rules

- No comments in code.
- No emojis in code or docs.
- Use OOP with clear responsibilities and explicit interfaces.
- Apply Clean Architecture boundaries.
- Follow SOLID principles.

## Architectural Expectations

- Keep the domain layer independent from FastAPI, file I/O, and external APIs.
- Use dependency inversion so use cases depend on abstractions, not concrete adapters.
- Add new features through use cases and adapters rather than embedding logic in routes.

