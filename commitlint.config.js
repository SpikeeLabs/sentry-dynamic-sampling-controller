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
    "body-empty": [2, "never", true],
    "scope-enum": [2, "always", scope],
  },
};
