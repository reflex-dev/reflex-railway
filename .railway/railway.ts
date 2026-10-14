// Railway Infrastructure as Code for this template: the Reflex app, Postgres
// and Redis as three services. Apply it to your own project with
//   cd .railway && npm install && railway config plan && railway config apply
// Point `REPO` at your fork first.
import { defineRailway, github, postgres, project, redis, service } from "railway/iac";

const REPO = "reflex-dev/reflex-railway";

export default defineRailway(() => {
  const db = postgres("Postgres");
  const cache = redis("Redis");

  const app = service("Reflex", {
    source: github(REPO, { branch: "main" }),
    preDeploy: "alembic upgrade head",
    healthcheck: "/_health",
    env: {
      PORT: "8080",
      DATABASE_URL: db.env.DATABASE_URL,
      REFLEX_REDIS_URL: cache.env.REDIS_URL,
      GRANIAN_WORKERS: "2",
    },
  });

  return project("Reflex", { resources: [app, db, cache] });
});
