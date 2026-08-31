MAX_PATCH_CHARS = 12000
MAX_FILE_CONTEXT_CHARS = 20000
MAX_OUTPUT_TOKENS = 300
MAX_COMMENTS = 5

SUPPORTED_EXTENSIONS = (".js", ".jsx", ".ts", ".tsx", ".py", ".yaml", ".yml")
SKIP_EXTENSIONS = (".css", ".json", ".lock", ".txt", ".gitignore", ".properties", ".md")

NODEJS_PROMPT = """
You are reviewing a Node.js / React / TypeScript diff.

Focus on:
- logic bugs
- missing null/undefined checks
- async/await mistakes
- state handling issues
- validation problems
- error handling
- security issues
- performance problems
- missing tests when important

Use surrounding file context to understand behavior.
Only comment on issues introduced by the diff or directly affected by it.
Do not comment on unrelated existing code unless the diff makes it problematic.

Return ONLY valid JSON:
{
  "comments": [
    {
      "line": 12,
      "side": "RIGHT",
      "body": "short comment"
    }
  ]
}

Rules:
- Max __MAX_COMMENTS__ comments
- Only actionable issues
- Keep comments short
"""

PYTHON_PROMPT = """
You are reviewing a Python diff.

Focus on:
- logic bugs
- exception handling
- type safety
- edge cases
- security issues

Use surrounding file context to understand behavior.
Only comment on issues introduced by the diff or directly affected by it.

Return ONLY valid JSON:
{
  "comments": [
    {
      "line": 12,
      "side": "RIGHT",
      "body": "short comment"
    }
  ]
}

Rules:
- Max __MAX_COMMENTS__ comments
- Only actionable issues
- Keep comments short
"""

K8S_PROMPT = """
You are reviewing Kubernetes YAML.

Focus on:
- apiVersion correctness
- resource limits
- probes
- securityContext
- service wiring
- selector/label mismatches
- invalid field placement

Use surrounding file context to understand whether this is truly a Kubernetes manifest.
Only comment on issues introduced by the diff or directly affected by it.

Return ONLY valid JSON:
{
  "comments": [
    {
      "line": 12,
      "side": "RIGHT",
      "body": "short comment"
    }
  ]
}

Rules:
- Max __MAX_COMMENTS__ comments
- Only actionable issues
- Keep comments short
"""

DEFAULT_PROMPT = """
You are reviewing code.

Focus on:
- correctness
- security
- reliability

Use surrounding file context to understand behavior.
Only comment on issues introduced by the diff or directly affected by it.

Return ONLY valid JSON:
{
  "comments": [
    {
      "line": 12,
      "side": "RIGHT",
      "body": "short comment"
    }
  ]
}

Rules:
- Max __MAX_COMMENTS__ comments
- Only actionable issues
- Keep comments short
"""

K8S_KINDS = {
    "deployment", "service", "ingress", "configmap", "secret", "statefulset",
    "daemonset", "job", "cronjob", "pod", "replicaset", "serviceaccount",
    "role", "clusterrole", "rolebinding", "clusterrolebinding", "networkpolicy",
    "persistentvolumeclaim", "horizontalpodautoscaler",
}

NON_K8S_YAML_NAMES = {
    "values.yaml", "values.yml",
    "chart.yaml", "chart.yml",
    "docker-compose.yml", "docker-compose.yaml",
    "application.yml", "application.yaml",
    "config.yml", "config.yaml",
    "settings.yml", "settings.yaml",
}

NON_K8S_PATH_HINTS = (
    "/.github/workflows/",
    "/config/",
    "/configs/",
)

K8S_PATH_HINTS = (
    "/k8s/",
    "/manifests/",
    "/templates/",
    "/deploy/",
    "/deployment/",
    "/helm/templates/",
)
