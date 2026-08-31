def ghGet(String url, String token, String apiVersion) {
  return sh(
    returnStdout: true,
    script: """
      set -euo pipefail
      curl -fsS \
        -H "Accept: application/vnd.github+json" \
        -H "Authorization: Bearer ${token}" \
        -H "X-GitHub-Api-Version: ${apiVersion}" \
        "${url}"
    """
  ).trim()
}

def ghPut(String url, String token, String apiVersion) {
  sh """
    set -euo pipefail
    curl -fsS -X PUT \
      -H "Accept: application/vnd.github+json" \
      -H "Authorization: Bearer ${token}" \
      -H "X-GitHub-Api-Version: ${apiVersion}" \
      "${url}"
  """
}

def ghDelete(String url, String token, String apiVersion) {
  sh """
    set -euo pipefail
    curl -fsS -X DELETE \
      -H "Accept: application/vnd.github+json" \
      -H "Authorization: Bearer ${token}" \
      -H "X-GitHub-Api-Version: ${apiVersion}" \
      "${url}"
  """
}

def syncGitHubAppRepos(Map args = [:]) {
  String apiBaseUrl        = (args.apiBaseUrl ?: '').trim()
  String org               = (args.org ?: '').trim()
  String installationId    = (args.installationId ?: '').toString().trim()
  String configFile        = (args.configFile ?: 'repo-sync.yml').trim()
  String githubAppCredId   = (args.githubAppCredId ?: '').trim()
  String patCredId         = (args.patCredId ?: '').trim()
  String apiVersion        = (args.apiVersion ?: '2022-11-28').trim()
  boolean dryRun           = (args.dryRun ?: false) as boolean

  if (!apiBaseUrl)     error('apiBaseUrl is required, for example https://ghe.example.com/api/v3')
  if (!org)            error('org is required')
  if (!installationId) error('installationId is required')
  if (!githubAppCredId) error('githubAppCredId is required')
  if (!patCredId)      error('patCredId is required')

  if (!fileExists(configFile)) {
    error("Config file not found: ${configFile}")
  }

  def cfg = readYaml file: configFile
  if (!(cfg instanceof Map) || cfg.isEmpty()) {
    error('Config file must be a non-empty YAML map like repo1: add')
  }

  def desiredFullNames = []
  def desiredLowerMap = [:]

  for (entry in cfg.entrySet()) {
    def rawName = entry.key.toString().trim()
    def action = entry.value == null ? '' : entry.value.toString().trim().toLowerCase()

    if (!rawName) {
      error('Repository name cannot be empty')
    }
    if (!(action in ['add', 'remove'])) {
      error("Invalid action for '${rawName}': '${entry.value}'. Use add or remove.")
    }

    def fullName = rawName.contains('/') ? rawName : "${org}/${rawName}"

    if (action == 'add') {
      if (!desiredLowerMap.containsKey(fullName.toLowerCase())) {
        desiredFullNames.add(fullName)
        desiredLowerMap[fullName.toLowerCase()] = true
      }
    }
  }

  if (desiredFullNames.isEmpty()) {
    error("At least one repo must be marked 'add'.")
  }

  withCredentials([
    usernamePassword(credentialsId: githubAppCredId, usernameVariable: 'GITHUB_APP_ID', passwordVariable: 'GITHUB_APP_TOKEN'),
    usernamePassword(credentialsId: patCredId, usernameVariable: 'GITHUB_USERNAME', passwordVariable: 'GITHUB_PAT'),
  ]) {
    def listUrl = "${apiBaseUrl}/installation/repositories?per_page=100"

    def currentRepoMap = [:]
    int page = 1

    while (true) {
      def response = ghGet("${listUrl}&page=${page}", env.GITHUB_APP_TOKEN, apiVersion)
      def parsed = readJSON text: response

      def repos = parsed.repositories ?: []
      for (repo in repos) {
        def fullName = (repo.full_name ?: "${repo.owner.login}/${repo.name}").toString()
        currentRepoMap[fullName.toLowerCase()] = [
          id: repo.id,
          full_name: fullName,
          name: repo.name
        ]
      }

      if (repos.size() < 100) {
        break
      }
      page++
    }

    def toAdd = []
    for (fullName in desiredFullNames) {
      if (!currentRepoMap.containsKey(fullName.toLowerCase())) {
        toAdd.add(fullName)
      }
    }

    def toRemove = []
    for (entry in currentRepoMap.entrySet()) {
      if (!desiredLowerMap.containsKey(entry.key)) {
        toRemove.add(entry.value)
      }
    }

    echo "Desired repos : ${desiredFullNames.sort()}"
    echo "Current repos : ${currentRepoMap.values().collect { it.full_name }.sort()}"
    echo "To add        : ${toAdd.sort()}"
    echo "To remove     : ${toRemove.collect { it.full_name }.sort()}"

    if (dryRun) {
      echo 'DRY_RUN enabled, no changes were applied.'
      return
    }

    for (fullName in toAdd) {
      def repoInfo = readJSON text: ghGet("${apiBaseUrl}/repos/${fullName}", env.GITHUB_PAT, apiVersion)
      def repoId = repoInfo.id
      echo "Adding ${fullName} (id: ${repoId}) to installation ${installationId}"
      ghPut("${apiBaseUrl}/user/installations/${installationId}/repositories/${repoId}", env.GITHUB_PAT, apiVersion)
    }

    for (repo in toRemove) {
      echo "Removing ${repo.full_name} (id: ${repo.id}) from installation ${installationId}"
      ghDelete("${apiBaseUrl}/user/installations/${installationId}/repositories/${repo.id}", env.GITHUB_PAT, apiVersion)
    }
  }
}

return this