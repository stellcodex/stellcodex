# DB Migrations (Templates)

These are SQL templates for V7-required tables/fields.

Apply via your migration tool (Alembic/Flyway/Prisma/etc).
After applying:
- decision_json must be NOT NULL
- rule_configs must exist and be used by the rule engine
