---
name: review-feature
description: Review a completed feature for correctness, security, architecture, requirements compliance, and code quality. Identify issues and recommend fixes without modifying files.
---

# Review Feature Skill

## Purpose

Perform a structured code review of an implemented feature before committing changes.

The goal is to identify real bugs, security vulnerabilities, missing requirements, architectural violations, and unnecessary complexity.

This skill is for reviewing code, not implementing fixes.

## 1. Understand the Project

Before reviewing:

1. Read the project `README.md`.
2. Read relevant documentation in `docs/`.
3. Read applicable project rules in `.cursor/rules/`.
4. Read `.cursor/skills/implement-feature/SKILL.md`.
5. Locate and read the approved feature implementation plan, if available.
6. Inspect the current Git changes using `git status` and `git diff`, including staged and untracked files relevant to the feature.

Do not assume that all uncommitted changes belong to the feature being reviewed.

If the approved plan or relevant documentation is missing, explicitly mention this limitation.

## 2. Review Scope

Review the feature specified by the user.

Inspect relevant frontend, backend, database, configuration, tests, and documentation changes.

Check the following areas:

### Requirements and Functionality
- Implementation matches the approved feature plan.
- All required functionality is implemented.
- Edge cases are handled.
- No unrelated functionality was introduced.

### Architecture
- Implementation follows the project's existing architecture and conventions.
- CQRS responsibilities are properly separated.
- Commands and queries follow established patterns.
- Event Sourcing is implemented consistently with project requirements.
- Domain events are recorded for relevant state changes.
- No unnecessary abstractions or architectural complexity were introduced.

### Security and Authentication
- Authentication and authorization are correctly enforced.
- Passwords and sensitive information are handled securely.
- Input validation is sufficient.
- Users cannot access or modify unauthorized resources.
- Sensitive information is not exposed in API responses or logs.

### Database
- Database operations are correct and consistent.
- Transactions are handled safely.
- Commit and rollback behavior is appropriate.
- Data integrity and relationships are preserved.
- Database access follows existing repository patterns.

### API and Error Handling
- API endpoints follow project conventions.
- HTTP status codes are appropriate.
- Validation errors are handled clearly.
- Unexpected failures are handled safely.
- API documentation matches the implementation.

### Frontend
- Frontend behavior matches the feature requirements.
- API integration is correct.
- Loading, success, and error states are handled.
- Input validation and user feedback are appropriate.

### Tests
- Relevant tests exist.
- Tests cover important success and failure scenarios.
- Security-sensitive and edge cases are tested.
- Identify missing tests that would catch meaningful bugs.

### Code Quality
- Code is readable and maintainable.
- Existing utilities and patterns are reused.
- No unnecessary dependencies or duplicated logic were introduced.
- The implementation remains appropriately simple for the project's scope.

## 3. Review Principles

- Prioritize correctness, security, and project requirements over stylistic preferences.
- Follow the project's actual documented architecture rather than imposing new architectural patterns.
- Do not recommend overengineering.
- Distinguish confirmed problems from potential risks.
- Do not report speculative issues as confirmed bugs.
- Do not invent requirements that are not documented.
- Do not suggest unrelated refactoring.
- If an implementation choice is valid and consistent with the project, do not flag it merely because another approach is possible.

## 4. Review Report

Produce a structured report.

### Summary

Include:
- Feature reviewed
- Files reviewed
- Overall assessment
- Number of issues by severity
- Any review limitations

### Findings

For each issue provide:

**Issue [number]: [Short title]**

- **Severity:** Critical / High / Medium / Low
- **Location:** File path and relevant function or line
- **Problem:** Explain the issue and cite the relevant code.
- **Impact:** Explain when and why it matters.
- **Recommended fix:** Suggest a practical solution consistent with the project.

Severity definitions:

- **Critical:** Severe security vulnerability, data loss, or fundamental system failure.
- **High:** Significant functional bug, security weakness, or major architectural violation.
- **Medium:** Important inconsistency, missing validation, or reliability issue.
- **Low:** Minor maintainability, documentation, or code-quality issue.

Order findings from highest to lowest severity.

### Missing Tests

List important missing test scenarios separately, without duplicating issues already reported.

### Final Recommendation

Conclude with one of:

- **Ready to commit** — No significant issues found.
- **Ready after minor fixes** — Only low-severity issues remain.
- **Changes required** — Medium or high-severity issues need attention.
- **Blocked** — Critical issues must be resolved.

Explain the recommendation briefly.

## 5. Approval Gate

**Do not modify any project files during the review.**

Do not:
- Implement fixes.
- Refactor code.
- Modify tests or documentation.
- Create commits.
- Apply automatic formatting.
- Run commands that modify project files or database state.

Read-only inspection and safe, non-mutating checks are allowed.

After presenting the report, wait for explicit user approval before making any changes.

If approval is given, fix only the approved issues and follow the project's `implement-feature` conventions where applicable.