const scope = [
  "admin",
  "command",
  "model",
  "route",
  "task",
  "validator",
  "metrics"
];

module.exports = {
  extends: ["@commitlint/config-angular"],
  rules: {
    "scope-enum": [2, "always", scope],
  },
};
