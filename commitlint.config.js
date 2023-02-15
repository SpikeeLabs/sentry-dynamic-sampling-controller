const scope = [
  "admin",
  "command",
  "model",
  "route",
  "task",
  "validator",
  "metrics",
  "panic",
  "sentry-api",
  "graph",
  "detector"
];

module.exports = {
  extends: ["@commitlint/config-angular"],
  rules: {
    "scope-enum": [2, "always", scope],
  },
};
