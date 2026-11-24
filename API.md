# Extra Time API

Base URL: `http://localhost:8000/api/` (or `http://localhost:8080/api/` through nginx). Swagger UI: `/api/docs/`; OpenAPI schema: `/api/schema/`.

- **Auth column**: *public* needs nothing; *access* needs `Authorization: Bearer <access token>`; *cookie* uses the `refresh_token` cookie set by login.
- Requests and responses are JSON.
- Lists are paginated, 20 per page (`?page=2`), as `{count, next, previous, results}`, except `/quiz/` and `/leaderboard/`, which return plain arrays.
- Errors use Django REST Framework's shape:
  - `400` returns field errors, e.g. `{"username": ["A user with that username already exists."]}` or `{"non_field_errors": [...]}`;
  - `401`, `403` and `404` return `{"detail": "..."}`;
  - `405` means the method isn't allowed on that endpoint.

## Auth

| Method and path | Auth | Body | Success | Errors |
|---|---|---|---|---|
| `POST /auth/signup/` | public | `{username, password, favorite_club?, country?}` | `201 {id, username}`. Creates the user and their profile | `400` field errors (taken username; weak password from Django's validators) |
| `POST /auth/login/` | public | `{username, password}` | `200 {access, user: Me}` and sets the refresh cookie | `401 {"detail": "Invalid username or password."}`. A failed login leaves an existing cookie alone |
| `POST /auth/refresh/` | cookie | — | `200 {access}` and replaces the cookie with a new refresh token; the old one is blacklisted | `401` if the cookie is missing, invalid, expired or blacklisted. The cookie is deleted, except when its token was rotated away by another tab's refresh |
| `POST /auth/logout/` | cookie (optional) | — | `204`. Blacklists the cookie's refresh token and deletes the cookie | — |

Refresh cookie: `refresh_token`, `HttpOnly`, `SameSite=Strict`, `Path=/api/auth/`, `Max-Age` = refresh lifetime, `Secure` when `JWT_COOKIE_SECURE=1`. The refresh token never appears in a response body.

## Current user

`Me` = `{id, username, date_joined, profile: {favorite_club, country, bio}, stats: {attempts, total_correct, best_score_pct}}`

| Method and path | Auth | Body | Success | Errors |
|---|---|---|---|---|
| `GET /me/` | access | — | `200 Me` | `401` |
| `PATCH /me/` | access | `{username?, profile?: {favorite_club?, country?, bio?}}` | `200 Me` | `400 {"username": [...]}` (taken or invalid), `401` |
| `DELETE /me/` | access | `{password}` | `204`. Blacklists all the user's refresh tokens, deletes the cookie, the user, their profile, attempts and questions | `400 {"password": ["The password is incorrect."]}`, `401` |
| `POST /me/password/` | access | `{old_password, new_password}` | `200 {access}` and a new refresh cookie. Every earlier refresh token of the user is blacklisted | `400 {"old_password": [...]}` or `{"new_password": [...]}`, `401` |

## Eras

`Era` = `{id, name, start_year, end_year, summary, created_at, updated_at}`

| Method and path | Auth | Success | Errors |
|---|---|---|---|
| `GET /eras/` | public | `200` page of eras, ordered by `start_year` | — |
| `POST /eras/` | access, staff | `201 Era` | `400` (`end_year` before `start_year`, duplicate name), `401`, `403` |
| `GET /eras/{id}/` | public | `200 Era` | `404` |
| `PUT /eras/{id}/`, `PATCH /eras/{id}/` | access, staff | `200 Era` | `400`, `401`, `403`, `404` |
| `DELETE /eras/{id}/` | access, staff | `204`. Deletes the era's questions; past attempts keep their snapshot | `401`, `403`, `404` |

## Topics

`Topic` = `{id, name, slug, description, created_at, updated_at}`. Same endpoints and permissions as eras: `GET /topics/` and `GET /topics/{id}/` public; `POST`, `PUT`, `PATCH`, `DELETE` staff only.

## Questions

`Question` = `{id, text, difficulty, explanation, era, era_name, topics: [id], topic_names: [str], author: username, choices: [{id, text, is_correct}], created_at, updated_at}`

`explanation` and every `is_correct` are left out unless the caller is the question's author or staff.

| Method and path | Auth | Body | Success | Errors |
|---|---|---|---|---|
| `GET /questions/` | public | — | `200` page of questions | — |
| `GET /questions/?mine=true` | access | — | `200` page of the caller's own questions, with answers | `401` |
| `POST /questions/` | access | `{text, difficulty, explanation, era, topics: [id], choices: [{text, is_correct}]}` | `201 Question`, `author` = caller | `400` (e.g. `{"choices": ["Exactly one choice must be marked correct."]}`; 2–4 choices required), `401` |
| `GET /questions/{id}/` | public | — | `200 Question` | `404` |
| `PUT /questions/{id}/` | access, author or staff | same as POST; `choices` replaces the whole set | `200 Question` | `400`, `401`, `403`, `404` |
| `PATCH /questions/{id}/` | access, author or staff | any fields; `choices` optional (replaces the set when given) | `200 Question` | `400`, `401`, `403`, `404` |
| `DELETE /questions/{id}/` | access, author or staff | — | `204`. Past attempts keep their snapshot | `401`, `403`, `404` |

`difficulty` is `easy`, `medium` or `hard`.

## Choices

`Choice` = `{id, question, text, is_correct, created_at, updated_at}` (`is_correct` only for the question's author and staff). The app writes choices through the question endpoints; this resource exists for standalone CRUD.

| Method and path | Auth | Success | Errors |
|---|---|---|---|
| `GET /choices/`, `GET /choices/{id}/` | public | `200` | `404` |
| `POST /choices/` | access, author of the question or staff | `201 Choice` | `400 {"question": [...]}` if the question would no longer have 2–4 choices with exactly one correct; `401`; `403` |
| `PUT`, `PATCH /choices/{id}/` | access, author of the question or staff | `200 Choice` | same as POST, plus `400` for moving the choice to another question, and `404` |
| `DELETE /choices/{id}/` | access, author of the question or staff | `204` | `400` if it would leave fewer than 2 choices or no correct one; `401`, `403`, `404` |

## Quiz

| Method and path | Auth | Success | Errors |
|---|---|---|---|
| `GET /quiz/?era={id}&topic={id}&count={n}` | access | `200` array of random questions, without answers and never written by the caller. `era` and `topic` are optional; `count` defaults to 10 and is clamped to 5–20. Fewer matching questions → a shorter array; none → `[]` | `400` unknown `era`/`topic` id or non-number `count`; `401` |

## Attempts

`Attempt` = `{id, era_name, topic_name, score, total, percent, created_at, answers: [{question, question_text, chosen_text, correct_text, is_correct, explanation}]}`

`question` is `null` and `explanation` is `""` once the question has been deleted; the texts are a snapshot taken when the round was submitted. `chosen_text` is `""` for a skipped question.

| Method and path | Auth | Body | Success | Errors |
|---|---|---|---|---|
| `GET /attempts/` | access | — | `200` page of the caller's attempts, newest first (staff: everyone's) | `401` |
| `POST /attempts/` | access | `{era?, topic?, answers: [{question: id, choice: id \| null}]}` | `201 Attempt`. Scored on the server and revealing the correct answers. A `choice` id that no longer exists counts as skipped | `400` empty `answers`, a question answered twice, a choice from another question, or the caller's own question; `401` |
| `GET /attempts/{id}/` | access | — | `200 Attempt` | `401`; `404` for someone else's attempt |
| `DELETE /attempts/{id}/` | access | — | `204` | `401`, `404` |
| `PUT`, `PATCH /attempts/{id}/` | access | — | — | `405`: attempts can't be edited |

## Leaderboard

| Method and path | Auth | Success |
|---|---|---|
| `GET /leaderboard/` | public | `200` array of up to 20 rows `{rank, username, favorite_club, attempts, total_correct, best_score_pct}`. Players with at least one attempt, ordered by `total_correct`, then `best_score_pct`, then who played first |
