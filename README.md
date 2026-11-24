# Extra Time

A quiz about the history of football, from the founding of the Football Association in 1863 to the 48-team World Cup in 2026.

Anyone can browse the question bank and the leaderboard. Logged-in players play rounds of 5 to 20 questions filtered by era or topic, get their score with an explanation for every answer, keep a history of their rounds, write their own questions, and manage their profile.

Built for HW4 of Web Application Development (KBTU, autumn 2026): a Django REST Framework API with JWT authentication, a Vue 3 + TypeScript frontend, and PostgreSQL, each in its own Docker Compose service.

## How the assignment is covered

| Requirement | Where |
|---|---|
| At least 3 entities with one-to-one, one-to-many and many-to-many relationships | `User`–`Profile` (1:1), `Era`→`Question`, `Question`→`Choice`, `User`→`QuizAttempt` (1:N), `Question`↔`Topic` and `QuizAttempt`↔`Question` through `AttemptAnswer` (M:N). See [Data model](#data-model) |
| Every table has at least 10 rows | `python manage.py seed` runs on first start: 11 users and profiles, 10 eras, 10 topics, 57 questions, 228 choices, 13 attempts with 73 answers |
| Full CRUD, public GET, authenticated writes | Every resource has list/retrieve/create/update/delete endpoints. Reads are public; every POST/PUT/PATCH/DELETE needs a JWT. See [API.md](API.md) |
| Signup, login, JWT | `djangorestframework-simplejwt`: `/api/auth/signup/`, `/api/auth/login/`, `/api/auth/refresh/`, `/api/auth/logout/` |
| At least 2 protected frontend routes, including Profile | `/profile`, `/play`, `/results`, `/my-questions` all require login |
| Profile shows the user and lets them change username and password | `/profile`, backed by `GET/PATCH/DELETE /api/me/` and `POST /api/me/password/` |
| API errors, loading states, JWT handling in the frontend | Every page has loading, error-with-retry and empty states; form errors appear under their fields; expired access tokens are refreshed and the request retried |
| Frontend, backend and database as separate Compose services | `frontend` (nginx), `backend` (Django), `db` (PostgreSQL 16) |
| README with setup instructions and a Postman collection | This file and [`postman/`](postman/) |

## Run it

Requirements: Docker Desktop (or Docker Engine) with Compose v2. Ports 8000 and 8080 must be free.

```bash
git clone <repo-url> extra-time
cd extra-time
cp .env.example .env
docker compose up --build
```

On the first start the backend applies migrations and seeds the database. When the logs show `Starting development server at http://0.0.0.0:8000/`, open http://localhost:8080/.

| URL | What |
|---|---|
| http://localhost:8080/ | The app (nginx serves the Vue build and forwards `/api/`, `/admin/`, `/static/` to Django) |
| http://localhost:8000/api/ | API root |
| http://localhost:8000/api/docs/ | Swagger UI. Click **Authorize** and paste an access token to call protected endpoints |
| http://localhost:8000/api/schema/ | OpenAPI 3 schema |
| http://localhost:8000/admin/ | Django admin (log in as `admin`) |

Useful commands:

```bash
docker compose exec backend python manage.py test accounts quiz   # backend tests
docker compose logs -f backend                                    # follow the backend log
docker compose down                                               # stop, keep the database
docker compose down -v                                            # stop and delete the database (re-seeds on next start)
```

### Demo accounts

| Username | Password | Role |
|---|---|---|
| `admin` | `admin12345` | Superuser: Django admin, can write eras and topics |
| `curator` | `football123` | Staff: wrote most seeded questions, can edit any question |
| `tifosi_luca`, `kop_end_sam`, `ultras_ana`, `kaiser_jonas`, `porteno_mateo`, `samba_bia`, `oranje_daan`, `culer_marta`, `almaty_arman` | `football123` | Players with profiles, past rounds and one question each |

The passwords come from `SEED_PASSWORD`, `ADMIN_USERNAME` and `ADMIN_PASSWORD` in `.env`.

### Environment variables

| Variable | Used by | Default in `.env.example` | Purpose |
|---|---|---|---|
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | db, backend | `extratime` / `extratime` / `change-me` | Database the postgres image creates and Django connects to |
| `DB_HOST`, `DB_PORT` | backend | `db`, `5432` | Where Django finds PostgreSQL: the Compose service name on the private network |
| `DJANGO_SECRET_KEY` | backend | placeholder | Signs JWTs and sessions. Change it for anything but local use |
| `DJANGO_DEBUG` | backend | `1` | `1`/`true` turns debug mode on |
| `DJANGO_ALLOWED_HOSTS` | backend | `localhost,127.0.0.1` | Host names Django serves |
| `JWT_ACCESS_MINUTES` | backend | `5` | Access token lifetime |
| `JWT_REFRESH_DAYS` | backend | `1` | Refresh token (and cookie) lifetime |
| `JWT_COOKIE_SECURE` | backend | `0` | `1` adds `Secure` to the refresh cookie; keep `0` for plain http on localhost |
| `SEED_PASSWORD` | backend | `football123` | Password of the seeded curator and players |
| `ADMIN_USERNAME`, `ADMIN_PASSWORD` | backend | `admin`, `admin12345` | Seeded superuser |

## Architecture

```
  Browser                                      Postman / Swagger UI
     |  http://localhost:8080                        |  http://localhost:8000
     v                                               |
 +---|------------------- network: quiz-net (bridge) |-------------------------+
 |   v                                               v                         |
 | +-----------------------+   /api/  /admin/   +------------------------+     |
 | | frontend              |   /static/         | backend                |     |
 | | nginx:1.27-alpine     | -----------------> | Django 5.2 + DRF       |     |
 | | serves the Vue build, |    backend:8000    | simplejwt, :8000       |     |
 | | SPA fallback          |                    | entrypoint: migrate -> |     |
 | +-----------------------+                    | seed -> runserver      |     |
 |                                              +-----------+------------+     |
 |                                                          | db:5432          |
 |                                              +-----------v------------+     |
 |                                              | db  postgres:16        |     |
 |                                              | healthcheck pg_isready |     |
 |                                              | port not published     |     |
 |                                              +-----------+------------+     |
 +----------------------------------------------------------|------------------+
                                                 named volume pgdata
```

- The browser only ever talks to `localhost:8080`. nginx serves the app and forwards API calls, so the app and the API share one origin.
- nginx resolves `backend` through Docker's DNS on every request, so it starts even when the backend is down and answers `502` within a few seconds instead of hanging.
- The backend waits for the database healthcheck (`depends_on: condition: service_healthy`). The database port is not published to the host.
- `pgdata` keeps the data across `docker compose down`; only `down -v` deletes it.

## Data model

All models have `created_at` and `updated_at`. Users are Django's built-in `User`.

| Model | Fields | Relationships |
|---|---|---|
| `Profile` | `favorite_club`, `country`, `bio` | **1:1** with `User` (created by a `post_save` signal) |
| `Era` | `name` (unique), `start_year`, `end_year`, `summary` | **1:N** an era has many questions |
| `Topic` | `name` (unique), `slug` (unique), `description` | **M:N** with `Question` |
| `Question` | `text`, `difficulty` (easy/medium/hard), `explanation`, `era`, `topics`, `author` | **N:1** `Era`, **N:1** `User` (author), **1:N** choices, **M:N** topics |
| `Choice` | `question`, `text`, `is_correct` | **N:1** `Question`. Each question has 2–4 choices, exactly one correct |
| `QuizAttempt` | `user`, `era` (optional), `topic` (optional), `score`, `total` | **N:1** `User`; **M:N** with `Question` through `AttemptAnswer` |
| `AttemptAnswer` | `attempt`, `question`, `choice` (empty = skipped), `is_correct`, `question_text`, `chosen_text`, `correct_text` | Through model of attempt ↔ question; unique per (attempt, question) |

Rules enforced by the API and the Django admin: an era can't end before it starts; a question always has 2–4 choices with exactly one correct (also when a single choice is added, changed or deleted through `/api/choices/`), and a choice can't move to another question; a chosen answer must belong to its question, and one whose choice was deleted since (the author edited the question mid-round) counts as skipped; players can't answer their own questions.

**Past rounds never change.** `AttemptAnswer` keeps a copy of the question text, the chosen answer and the correct answer, and its links to the question and choice become empty if those are deleted. Editing or deleting a question (or its era) therefore never changes a past score or result page.

## How auth works

### What a JWT is

A JSON Web Token is three base64url parts joined by dots: `header.payload.signature`.

- **Header**: the algorithm, here `{"alg": "HS256", "typ": "JWT"}`.
- **Payload** (claims): `token_type` (`access` or `refresh`), `exp` (expiry, Unix time), `iat` (issued at), `jti` (unique token id) and `user_id`. It is encoded, not encrypted: anyone holding the token can read it, so it carries no secrets.
- **Signature**: HMAC-SHA256 of `header.payload` with `DJANGO_SECRET_KEY`. Changing a single character of the payload breaks the signature, and the server rejects the token.

The server keeps no session for access tokens: it verifies the signature and `exp` on every request and reads `user_id` from the payload.

### Access and refresh tokens

| | Access token | Refresh token |
|---|---|---|
| Lifetime | 5 minutes (`JWT_ACCESS_MINUTES`) | 1 day (`JWT_REFRESH_DAYS`) |
| Sent as | `Authorization: Bearer <token>` header | `refresh_token` cookie, only to `/api/auth/` |
| Used for | Every protected API call | Getting a new access token |
| Stored in the browser | A JavaScript variable in memory (`frontend/src/auth/session.ts`) | An `HttpOnly`, `SameSite=Strict` cookie JavaScript can't read |
| Revocation | Expires quickly | Blacklisted on logout, on rotation and on password change |

**Why this storage.** If an attacker manages to run JavaScript on the page (XSS), anything in `localStorage` or in a readable cookie can be stolen and used from anywhere. Here the long-lived refresh token is in an `HttpOnly` cookie that scripts can't read. The access token is only in memory, and it expires within 5 minutes. `SameSite=Strict` means the browser never attaches the cookie to a request started by another site, so a forged cross-site request can't refresh a session. Because nginx serves the app and the API from the same origin, the cookie works without any CORS configuration. The cookie's `Path=/api/auth/` keeps it off every other request. A reload loses the in-memory access token; the app gets a new one from the cookie before showing any page.

**Rotation and the blacklist.** Every `POST /api/auth/refresh/` returns a new access token and replaces the cookie with a new refresh token; the old refresh token goes on the blacklist (`ROTATE_REFRESH_TOKENS`, `BLACKLIST_AFTER_ROTATION`). A stolen refresh token therefore works at most once. Logging out blacklists the cookie's token and deletes the cookie. Changing the password blacklists every refresh token the user has ever been issued, so all other devices are logged out, and returns a fresh pair to the device that made the change. Deleting the account does the same before removing the user.

### Backend: who may do what

Default for every endpoint (`REST_FRAMEWORK` in `backend/config/settings.py`): `JWTAuthentication` and `IsAuthenticatedOrReadOnly`, so reads are public and any write without a valid token gets `401`. Each view narrows it further (`backend/quiz/permissions.py`):

| Resource | Read | Create | Update / delete |
|---|---|---|---|
| `/api/eras/`, `/api/topics/` | anyone | staff (`IsStaffOrReadOnly`) | staff |
| `/api/questions/` | anyone | any logged-in user, who becomes the author | author or staff (`IsAuthorOrStaffOrReadOnly`), else `403` |
| `/api/choices/` | anyone | author of the parent question or staff | author of the parent question or staff |
| `/api/attempts/` | own only (staff: all); others' ids give `404` | logged-in user | delete own; editing gives `405` |
| `/api/quiz/` | logged-in user | — | — |
| `/api/leaderboard/` | anyone | — | — |
| `/api/me/`, `/api/me/password/` | logged-in user, only themselves | — | — |

Answers stay secret on the server: `is_correct` and `explanation` are only included in a question for its author and staff. `/api/quiz/` never includes them, not even for staff. A player sees the correct answers only in the result of their own submitted round.

### Frontend: route guard and refresh flow

- Routes carry `meta.requiresAuth` or `meta.guestOnly` (`frontend/src/router.ts`). Before the first navigation, the guard waits for `initSession()`, which calls `/api/auth/refresh/` once with the cookie and, if that works, loads `/api/me/`. So a reload on `/profile` restores the session before the guard decides, and the login page never flashes.
- A logged-out visit to a protected route redirects to `/login?redirect=/that/path`; after logging in the app returns there. Logged-in users who open `/login` or `/signup` go to `/`.
- `frontend/src/api/client.ts` adds the `Bearer` header to every request. When a non-auth request gets `401` (usually an expired access token), it calls `refreshAccessToken()` and retries the request once. Requests that fail at the same moment share a single refresh call, and open tabs take turns through a Web Lock: with rotation, a second refresh with the same cookie would send an already-blacklisted token. If one slips through anyway, the server answers `401` but keeps the cookie, because the other tab may already hold its replacement. If the refresh fails, the session is cleared and the user is sent to `/login?redirect=…`.
- This is what keeps a long quiz safe: if the access token expires while someone is answering, submitting the round refreshes the token silently and the answers are saved.

## Postman

Import [`postman/extra-time.postman_collection.json`](postman/extra-time.postman_collection.json) and the **Extra Time Local** environment ([`postman/extra-time.postman_environment.json`](postman/extra-time.postman_environment.json), `base_url = http://localhost:8000`), then run the whole collection with the Collection Runner, or from the command line:

```bash
npx newman run postman/extra-time.postman_collection.json -e postman/extra-time.postman_environment.json
```

The 62 requests run top to bottom, and every request has a status test (85 assertions in all):

- **Auth**: sign up a unique user, log in (the access token goes into `{{access}}`; Postman keeps the refresh cookie), read `/me/`, refresh, change username, change password, log out, check that refreshing after logout gives `401`, log in again. It also logs in a seeded player (`{{other_access}}`) and `admin` (`{{admin_access}}`) for later folders.
- **Eras**, **Topics** (as admin), **Questions**, **Choices**: full CRUD, saving the new ids to collection variables.
- **Quiz & Attempts**: get 5 questions, submit answers, read the attempt, editing gives `405`, another player gets `404`.
- **Leaderboard**.
- **Errors**: anonymous write `401`, player creating an era `403`, editing someone else's question `403`, invalid input `400`.
- **Cleanup**: deletes everything it created, then the Postman account itself, so the collection can run again.

## Frontend

| Route | Access | Page |
|---|---|---|
| `/` | public | Intro, era timeline (each era starts a quiz on it), top 5 of the leaderboard |
| `/questions`, `/questions/:id` | public | Question bank (paginated) and question detail without the answer |
| `/leaderboard` | public | Top 20 players |
| `/login`, `/signup` | guests only | Forms with errors under each field |
| `/play` | login | Choose era, topic and length → one question at a time → score and explanations |
| `/results`, `/results/:id` | login | Past rounds; open one to review it or delete it |
| `/my-questions`, `/my-questions/new`, `/my-questions/:id/edit` | login | Write, edit and delete your own questions |
| `/profile` | login | Stats, recent rounds, change username and profile, change password, delete account, log out |

| Path | Role |
|---|---|
| `src/api/client.ts` | `fetch` wrapper: Bearer header, 401 → refresh → retry, `ApiError`, field errors |
| `src/api/resources.ts`, `src/api/types.ts` | One function per endpoint and the JSON shapes |
| `src/auth/session.ts` | In-memory access token, current user, login/signup/logout, shared refresh |
| `src/router.ts` | Routes and the guard |
| `src/composables/useAsync.ts` | Loading/error state for a request |
| `src/components/`, `src/views/` | Reusable pieces and one view per route |

For development without Docker, run the backend in Compose and `cd frontend && npm install && npm run dev`; Vite proxies `/api` to `localhost:8000`.

## Known limitations

- Answers can be learned from your own past results: there is no server-side quiz session, so a player can play a round, read the answers and score better on a later round. Rounds only exclude the player's own questions.
- Questions written by players go live at once, with no review step.
- Local Docker only: the Django development server, plain http and `DEBUG=1`.

## Repository layout

```
backend/            Django project
  config/           settings (from .env), urls
  accounts/         Profile, signup/login/refresh/logout, /me/ endpoints, refresh cookie helpers
  quiz/             Era, Topic, Question, Choice, QuizAttempt, AttemptAnswer; CRUD, quiz, attempts, leaderboard
    seed_data/      JSON loaded by `python manage.py seed`
frontend/           Vue 3 + TypeScript app, nginx config, Dockerfile
postman/            Postman collection and environment
API.md              Endpoint reference
docker-compose.yml  db, backend, frontend
```
