# Database Scripts

## MongoDB Atlas
1. Create a cluster in MongoDB Atlas.
2. Set `MONGODB_URI` in `Backend/.env`.
3. Optional: run `mongodb_indexes.js` in `mongosh`.
4. Start backend: `uvicorn app.main:app --reload`.
5. Until `MONGODB_URI` is set, DB endpoints return `503` by design.

## Legacy PostgreSQL
`postgresql_schema.sql` is kept only for reference from earlier setup.
