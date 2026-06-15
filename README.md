Django E‑Commerce REST API
A production‑ready backend for online stores built with Django, Django REST Framework, and PostgreSQL. Designed for secure authentication, reliable payments, and scalable performance.

Core Features
Full REST API using Django + DRF + Sqlite3 or PostgreSQL in production

JWT authentication with rotation + blacklist

Stripe payments with webhook verification

Rate limiting (5–50 req/hr) and response caching (1–5 min)

Modular architecture with role‑based permissions

Search, filtering, CORS, logging, and Swagger/OpenAPI docs

Tech Stack
Backend: Django, DRF

Database: Sqlite3 or PostgreSQL in production

Auth: JWT (rotation + blacklist)

Payments: Stripe (PaymentIntent + webhooks)

Docs: OpenAPI / Swagger

Getting Started
Clone the repo

Install dependencies

Configure environment variables (DB, JWT, Stripe)

Run migrations + create superuser

Start the server and open Swagger docs

Operational Notes
Protected endpoints require JWT authentication

Stripe webhooks finalize payments securely

Rate limiting + caching improve performance and stability

Role‑based permissions control admin and management access
