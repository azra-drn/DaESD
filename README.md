# Bristol Regional Food Network / DaESD

BRFN is a Django marketplace project for local food ordering. It supports customers, community groups, restaurants, producers, and admins in one system. Users can browse products, add items to a cart, place multi-producer orders, review order history, manage recurring orders, and work with surplus deals. The project uses PostgreSQL through Docker Compose.

## Technologies Used

- Python
- Django
- PostgreSQL
- Docker
- Docker Compose
- HTML template views
- CSS styling
- Django authentication and role-based dashboards

## Running the Project with Docker

Start the project:

```bash
docker compose up --build -d
```

Apply migrations:

```bash
docker compose exec web python manage.py migrate
```

Load or refresh demo data:

```bash
docker compose exec web python manage.py seed_demo
```

If you want to fully rebuild the seeded marketplace data:

```bash
docker compose exec web python manage.py seed_demo --reset
```

Open the app in your browser:

- [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

View recent web logs:

```bash
docker compose logs web --tail=100
```

Stop the project:

```bash
docker compose down
```

## Database Information

The database runs in PostgreSQL through Docker Compose.

- Database name: `brfn_db`
- Database user: `brfn_user`
- Database password: `brfn_password`

Data is stored in a Docker volume, so it may still be there after restarting containers.

Open the database shell:

```bash
docker compose exec db psql -U brfn_user -d brfn_db
```

Useful `psql` commands:

```sql
\dt
\d table_name
\q
```

## Running Tests

Run the full Django test suite:

```bash
docker compose exec web python manage.py test
```

The test suite covers important flows such as:

- registration and role setup
- product browsing and filters
- cart and checkout
- order history and producer orders
- recurring orders
- surplus deals
- finance and settlements

If a stale test database already exists and Django asks about deleting it, rerun with a clean database strategy your team agrees on before the demo.

## Main User Roles

- Admin: manages the platform dashboard, finance reporting, and high-level overview pages
- Producer: lists products, manages stock, and reviews producer-side orders
- Customer: browses products, adds items to the cart, places orders, and checks order history
- Community group: uses the customer flow but is intended for larger or bulk orders
- Restaurant/business: uses the customer flow and can create recurring orders where supported

## Manual Testing Guide

After setup, it is worth checking these areas manually:

- register and log in for each role
- browse products and open product details
- add products to the cart
- add products from different producers
- confirm producer names show in the cart and checkout
- place an order and check order history
- open the producer dashboard and producer order views
- test recurring orders
- test surplus deals
- check colours, readability, and layout consistency

Specific coursework scenarios:

- `TC-017`: community group bulk multi-producer order
- `TC-018`: restaurant recurring weekly or fortnightly orders
- `TC-019`: producer surplus produce discounts

## Troubleshooting

Rebuild the containers:

```bash
docker compose up --build -d
```

Rerun migrations:

```bash
docker compose exec web python manage.py migrate
```

Check logs:

```bash
docker compose logs web --tail=100
docker compose logs db --tail=100
```

Open the database:

```bash
docker compose exec db psql -U brfn_user -d brfn_db
```

If the app is behaving strangely after code changes:

```bash
docker compose down
docker compose up --build -d
```

If static files or browser-side behavior seem stale, do a hard browser refresh.

## Notes for Markers and Team Members

- The project is best run through Docker for the most consistent setup.
- The application currently uses PostgreSQL, not MongoDB.
- Some features are demo-friendly rather than production-complete. For example, recurring orders behave like application-managed templates rather than a full background scheduling service.
- If you are checking a feature for marking or demo purposes, it is better to describe honestly what is implemented rather than over-claiming hidden automation.
