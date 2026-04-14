# Architecture Note
## 1. Context diagram:
*See Image 1 for diagram*

This diagram that was made on Excalidraw, represents the quotes app. This is the central
component and all external systems that it interacts with. Each arrow is labelled with the type of
data, or request it goes with.

The user interacts with the application over standard HTTP. The flask app queries the supabase-
hosted database to read and write save quotes. It also fetches a quote for ‘random quote of the day’

from ninjas quotes. Finally, GitHub Actions drives the CI/CD pipeline, building a Docker image that is
pushed to the GitHub Container Registry and automatically deployed to Render.

## 2. Integration points

### 2.1 Supabase database (PostgreSQL)

Table name: quotes

Key columns: id, quote, author, work, category, source

Purpose: Stored quotes into the database to be displayed.

This table above describes how key data is stored. The application uses Supabase as its managed
PostgreSQL provider.

### 2.2 External API (API Ninjas)
The application uses API Ninjas for these three features:
- Quote of the day
Fetches daily quote from API Ninjas, response is a JSON array, contains quote and
author, result is cached in the database for 24 hours.
- Random Quote
Calls API Ninjas on demand and displays the result directly.

- Quote generator
Also uses random endpoint, returning a new quote each time the user triggers it.

## 3. Branching Model
The team adopted a trunk-based development workflow with short-lived feature branches,
consistent with the CI/CD-first approach recommended for small teams in Lean/Agile
environments.

**Production branch:** main

main is always deployable. No direct commits are permitted — all changes enter via pull request
with a passing CI status check and at least one peer review approval.

**Feature branches:**

Each team member picks up a GitHub Issue and creates a branch from main. Branches are kept
short-lived. This minimises merge conflicts and keeps the integration surface small, a core
principle of trunk-based development.
Flow from issue to main:
1. Developer picks up a GitHub Issue from the Kanban board.
2. Feature branch created from latest main.
3. Commits pushed; pull request opened and linked to the issue.
4. GitHub Actions runs lint to test to build on the PR. All checks must pass.
5. At least one teammate reviews and approves the PR.
6. PR is squash-merged into main; issue is automatically closed.
7. CD pipeline triggers, Docker image built, pushed to GHCR, deployed to Render

---


# Team Collaboration Log

## 1. Overview
This is our team collaboration log for IS2209. This document shows our overall work as a group and
how we worked together. This involves who did what, how we kept in touch, and how the project
moved form an idea to a finished, fully functional application over the course of 5-6 weeks. The app
itself pulls quotes form a free third-party API and displays them through a full-stack web interface.

## 2. Team Roles and Responsibility
We divided up responsibilities early on, mostly based on what each person was most comfortable
with. The table below show each members role:

**Colm:** Backend Developer, Server-side logic, data handling, API integration. Collaborated closely with Ben throughout

**Ben:** Backend Developer, Server-side logic, data handling, API integration. Collaborated closely with Colm throughout

**Josh:** UI/Frontend Developer, All frontend views, styling, user-interface design. Owned all client-side code

**Cian:** Project Manager, GitHub Projects Board, issue tracking, sprint organisation. Managed team workflow and task visibility

Colm and Ben handled the backend between them. Rather than splitting it down the middle cleanly,
they worked side by side on the same areas including server logic, hooking up the API, and making
sure data was flowing correctly to the frontend. Josh had full ownership of everything the user
actually sees. This includes the layout, the styling, and making the interface work the way it should.
Cian kept the project board in order, which meant we always had a clear picture of what was done,
what was in progress, and what still needed attention.

## 3. Group Communication
We met up every week in person for the duration of the project. These were mainly just regular
catch ups to make sure everyone was on the same page before another week of work started. All
four of us attended each time, which helped keep things moving and meant nothing fell through the
cracks.

On top of our weekly meetings which usually occurred after the scheduled tutorials. We attended
tutorials each week throughout the duration of the project. These were useful for getting clarity on
requirements and checking in with the tutors if we were confused with parts of the project.

## 4. Projects Board
Cian looked after the board from start to finish. As work came in or got picked up, issues were
logged and moved through the stages. This gave us a shared view of where things were at any given
moment without needing to ask each other constantly. These stages included:
 - To Do 
 - In progress 
 - Review 
 - Done

## 5. Summary
Overall, this was a project where the team genuinely worked together rather than just dividing it
into four isolated pieces. Colm and Ben collaborated closely on the backend. Josh drove the
frontend, and Cian kept the project organised and visible through the board. We met every week
without fail and attended tutorials as a group.


---

# Toolchain Critique
## What Worked
### Supabase as a lightweight persistence layer
We used supabase-py with create_client() and .table.insert(). This took under 10 minutes to set
up and required no schema migrations or local database configuration. In practice, it saved us
from writing ~50 lines of SQLite boilerplate.
### Render + GitHub integration
Connecting our GitHub repo to Render meant every git push to main automatically redeployed
the app. After an initial misconfiguration (missing SUPABASE_URL env var — see below),
subsequent deploys took less than 60 seconds. This reduced our lead time (a Lean metric) from
commit to visible deployment from approximately 10 minutes (manual) to roughly 1 minute.
### Environment variables via python-dotenv
We stored API_KEY, SUPABASE_URL, and SUPABASE_KEY in a .env file loaded by load_dotenv().
This kept secrets out of app.py and followed 12-factor app config principles. When we later
moved to Render, we simply copied the same variables into Render's dashboard — no code
changes required.
### API-Ninjas external quote service
The API was reliable and had no authentication latency. We made three concurrent calls per
page load (quote of the day, random quote, category quote) and never hit rate limits during
testing.

## What We Would Change
**_Add automated testing (pytest was installed but never used)_**

We had pytest in requirements.txt but wrote zero tests. This was a mistake. When we later
changed the API response parsing, we had to manually reload the page five or six times to verify
it still worked.

What we would do differently: Write three tests from day one — first, that the API returns a
quote; second, that Supabase insert succeeds; third, that the Flask route returns a 200 status
code. Each test would take approximately five minutes to write and would have caught a
broken-parse error instantly.

**Fix the requirements misinterpretation (the dropdown fix)**

What we would do differently: Validate requirements against the database schema before
writing the first line of code. This would have saved approximately two hours of rework — a
classic Agile feedback loop failure, where we received feedback too late.

**Add error handling for API failures**

Currently, if API-Ninjas returns a 429 rate limit error or times out, the entire page crashes with a
requests.exceptions.RequestException. In production, this would show users a Flask debug
page — unacceptable.

What we would do differently: Wrap each requests.get() call in a try/except block, and serve a
fallback quote from Supabase. We would also add circuit breaker logic (a DevOps resilience
pattern) to stop calling the API after three consecutive failures.

**Add pre-commit hooks**

We had no linting or formatting enforcement. One team member committed a file with mixed
tabs and spaces, which passed CI (because we had no CI — see below) but later broke the
renderer on Render.

What we would do differently: Add ruff format --check as a pre-commit hook using pre-
commit.com. This would have rejected the bad commit immediately.

### Risks and Mitigations
API key leaked in commit

This did not happen because we used .env plus .gitignore. In production, we would mitigate by
rotating the key immediately and enabling GitHub secret scanning.

Supabase row explosion from duplicates
This did happen — we observed duplicates after twenty or more page refreshes. We would
mitigate by adding a unique constraint on (quote, author) in the production database.


## Connection to Module Theory (Lean, Agile, DevOps)
**Lean: Lead time**

Render auto-deploys reduced our commit-to-deploy time from approximately ten minutes
(manual) to roughly one minute. This was a measurable improvement.

**Lean: Waste**

Duplicate quote inserts represent pure data waste. Adding a unique constraint would eliminate
this waste entirely.

**Agile: Feedback loops**

Our requirements misinterpretation (the missing dropdown) took approximately two hours to
discover. One team member admitted: "I didn't read the brief right the first time." This was a
classic feedback loop failure.

**DevOps: CI/CD**

We had no continuous integration — broken code reached the main branch. Adding GitHub
Actions to run linting and tests on every pull request would close this loop. Notably, pytest was
in our requirements file but never ran automatically.

## Summary of Rubric Requirements
What worked: Supabase, Render, dotenv, and the API-Ninjas external quote service.
What we would change: Add pytest tests, prevent duplicate inserts, implement the dropdown
category fix, add error handling for API failures, and introduce pre-commit hooks.
Risks and mitigations: Covered above — including the actual duplicate-row incident, the
missing environment variable on first deploy, and the lack of CI/CD.
Connection to module theory: Tied to Lean (lead time and waste), Agile (feedback loops),
DevOps (CI/CD missing then proposed), and 12-factor (config via environment variables and
backing services as attached resources).