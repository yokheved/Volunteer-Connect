---
name: implement-feature
description: Implement a complete feature in the Volunteer Matching System according to the project specifications and architecture.
---

# Implement Feature

Use this skill when implementing a new feature or modifying an existing feature
in the Volunteer Matching System.

## Step 1 - Understand the feature

Before writing code:

1. Read the relevant files under `/docs`.
2. Identify the actors involved:
   - CLIENT
   - VOLUNTEER
   - or both.
3. Identify the expected inputs, outputs, and business rules.
4. Check whether the requested feature already exists or conflicts with an
   existing requirement.

Do not invent missing requirements. If an important requirement is unclear,
ask for clarification before implementing it.

## Step 2 - Classify operations

For every backend operation, determine whether it is:

- Command - changes system state.
- Query - reads data without changing system state.

Keep Commands and Queries separate according to the project's CQRS architecture.

Examples:

- Create volunteer request -> Command
- Approve volunteer request -> Command
- Reject volunteer request -> Command
- Search volunteers -> Query
- Get volunteer details -> Query
- Get upcoming volunteering activities -> Query

## Step 3 - Plan the implementation

Before modifying files, briefly state:

- Which files will be created.
- Which files will be modified.
- Which Command/Query is involved.
- Whether the database is affected.
- Whether an event should be recorded.

Prefer the smallest implementation that satisfies the requirement.

## Step 4 - Implement

Follow the project architecture rules.

Backend:
- Use Flask.
- Keep routes/controllers thin.
- Keep business logic outside routes.
- Separate Commands from Queries.
- Keep persistence logic separated from HTTP handling.

Frontend:
- Use React + Vite.
- Keep API access separate from presentation components.

Do not add unrelated features.

## Step 5 - Event Sourcing

For operations that change business state, determine whether a domain event
should be recorded.

Examples:

- VolunteerRequestCreated
- VolunteerRequestApproved
- VolunteerRequestRejected
- VolunteerRequestCompleted

Do not create unnecessary events for simple read operations.

## Step 6 - Test

Add or update appropriate tests for the feature.

At minimum verify:
- the expected successful flow;
- important validation;
- authorization/role restrictions when relevant.

## Step 7 - Verify

Before declaring the feature complete:

1. Check that the implementation matches the specification.
2. Check that CQRS separation is preserved.
3. Check that routes do not contain business logic.
4. Check that existing functionality was not unnecessarily changed.
5. Run relevant tests.
6. Report what was implemented and any remaining issues.