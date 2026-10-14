// Railway Infrastructure as Code for this template: four services, each
// deployed and scaled independently. Apply it to your own project with
//   cd .railway && npm install && railway config plan && railway config apply
// Point `REPO` at your fork first.
import { defineRailway, github, postgres, project, redis, service } from "railway/iac";

const REPO = "reflex-dev/reflex-railway";

export default defineRailway(() => {
  const db = postgres("Postgres");
  const cache = redis("Redis");

  const backend = service("Backend", {
    source: github(REPO, { branch: "main" }),
    preDeploy: "alembic upgrade head",
    healthcheck: "/_health",
    env: {
      RAILWAY_DOCKERFILE_PATH: "Dockerfile.backend",
      PORT: "8000",
      DATABASE_URL: db.env.DATABASE_URL,
      REFLEX_REDIS_URL: cache.env.REDIS_URL,
      GRANIAN_WORKERS: "2",
    },
  });

  const frontend = service("Frontend", {
    source: github(REPO, { branch: "main" }),
    healthcheck: "/healthz",
    env: {
      RAILWAY_DOCKERFILE_PATH: "Dockerfile.frontend",
      PORT: "8080",
      BACKEND_HOST: backend.env.RAILWAY_PRIVATE_DOMAIN,
      BACKEND_PORT: backend.env.PORT,
    },
  });

  return project("Reflex", { resources: [frontend, backend, db, cache] });
});
