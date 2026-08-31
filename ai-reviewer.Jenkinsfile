pipeline {
    agent {label 'linux'}

  options {
    timestamps()
    disableResume()
  }

  parameters {
    string(name: 'REPO_NAME', defaultValue: '', description: 'repo')
    string(name: 'REPO_FULL_NAME', defaultValue: '', description: 'owner/repo')
    string(name: 'PR_NUMBER', defaultValue: '', description: 'PR number')
    string(name: 'PR_ISSUE_NUMBER', defaultValue: '', description: 'PR number from issue_comment payload')
    string(name: 'ACTION', defaultValue: '', description: 'GitHub action, e.g. opened or created')
    string(name: 'COMMENT_BODY', defaultValue: '', description: 'PR comment body')
    string(name: 'PR_HTML_URL', defaultValue: '', description: 'PR HTML URL from pull_request events')
    string(name: 'PR_ISSUE_URL', defaultValue: '', description: 'PR API URL from issue_comment events')
    string(name: 'PR_HEAD_SHA', defaultValue: '', description: 'Head SHA from pull_request events')

    string(name: 'PR_STATE', defaultValue: '', description: 'PR state from pull_request payload')
    string(name: 'PR_MERGED', defaultValue: '', description: 'PR merged from pull_request payload')
    string(name: 'ISSUE_STATE', defaultValue: '', description: 'Issue state from issue_comment payload')
    string(name: 'GH_EVENT', defaultValue: '', description: 'GitHub event header (X-GitHub-Event)')
  }

triggers {
  GenericTrigger(
    tokenCredentialId: 'ai-review-webhook-token',
    causeString: 'AI review for $REPO_FULL_NAME#$PR_NUMBER',

    genericHeaderVariables: [
      [key: 'GH_EVENT', value: 'X-GitHub-Event']
    ],

    genericVariables: [
      [key: 'REPO_NAME',      value: '$.repository.name',                 expressionType: 'JSONPath', defaultValue: ''],
      [key: 'REPO_FULL_NAME', value: '$.repository.full_name',            expressionType: 'JSONPath', defaultValue: ''],
      [key: 'ACTION',         value: '$.action',                          expressionType: 'JSONPath', defaultValue: ''],

      // pull_request payload
      [key: 'PR_NUMBER',      value: '$.number',                          expressionType: 'JSONPath', defaultValue: ''],
      [key: 'PR_HTML_URL',    value: '$.pull_request.html_url',           expressionType: 'JSONPath', defaultValue: ''],
      [key: 'PR_HEAD_SHA',    value: '$.pull_request.head.sha',           expressionType: 'JSONPath', defaultValue: ''],
      [key: 'PR_STATE',       value: '$.pull_request.state',              expressionType: 'JSONPath', defaultValue: ''],
      [key: 'PR_MERGED',      value: '$.pull_request.merged',             expressionType: 'JSONPath', defaultValue: ''],

      // issue_comment payload (PR comments come through as issues)
      [key: 'PR_ISSUE_NUMBER', value: '$.issue.number',                    expressionType: 'JSONPath', defaultValue: ''],
      [key: 'COMMENT_BODY',    value: '$.comment.body',                    expressionType: 'JSONPath', defaultValue: ''],
      [key: 'PR_ISSUE_URL',    value: '$.issue.pull_request.url',          expressionType: 'JSONPath', defaultValue: ''],
      [key: 'ISSUE_STATE',     value: '$.issue.state',                     expressionType: 'JSONPath', defaultValue: ''],
    ],

    printContributedVariables: true,
    printPostContent: false,

    // Filter only what you want to trigger on:
    // 1) pull_request opened AND PR_STATE=open
    // 2) issue_comment created AND ISSUE_STATE=open AND contains /ai-review
    regexpFilterText: '$ACTION:$PR_STATE:$ISSUE_STATE:$PR_ISSUE_URL:$COMMENT_BODY',
    regexpFilterExpression: '^(opened:open:::.*|created::open:.+:(?s).*(^|\\s)/ai-review(\\s|$).*)$'
  )
}

  environment {
    REVIEW_API_URL = 'https://reviewer.example.com/review/pr'
    CHECK_NAME = 'AI Code Review'
  }

  stages {
    stage('Normalize and guard') {
      steps {
        script {
          def ghEvent = (env.GH_EVENT ?: '').trim()

          def action  = (env.ACTION ?: '').trim()
          def comment = (env.COMMENT_BODY ?: '').trim()
          def repo    = (env.REPO_FULL_NAME ?: '').trim()

          // Normalize PR number depending on event type
          def prNumber = (env.PR_NUMBER ?: '').trim()
          if (!prNumber) prNumber = (env.PR_ISSUE_NUMBER ?: '').trim()

          if (!repo || !prNumber) {
            error('Missing repository or PR number.')
          }

          def owner = repo.tokenize('/')[0]
          if (!owner || !repo.contains('/')) {
            error("Repository must be in owner/repository form: ${repo}")
          }

        def isPrOpenedEvent =
          (action == 'opened' &&
          (env.PR_STATE ?: '').trim() == 'open' &&
          ((env.PR_MERGED ?: 'false').trim() != 'true'))

        def isAiReviewCommentEvent =
          (action == 'created' &&
          (env.PR_ISSUE_URL ?: '').trim() &&                 // ensures it's a PR comment
          (env.ISSUE_STATE ?: '').trim() == 'open' &&        // ensures PR is open
          (comment ==~ /(?is).*(^|\s)\/ai-review(?:\s+.*)?(\s|$).*/))


          if (!(isPrOpenedEvent || isAiReviewCommentEvent)) {
            error("Rejected event: event=${ghEvent}, action=${action}, repo=${repo}, pr=${prNumber}, pr_state=${env.PR_STATE}, issue_state=${env.ISSUE_STATE}")
          }

          env.REPO_FULL_NAME = repo
          env.REPO_OWNER = owner
          env.PR_NUMBER = prNumber
          env.PR_URL = (env.PR_HTML_URL ?: env.PR_ISSUE_URL ?: '').trim()

          currentBuild.displayName = "${repo}#${prNumber}"
          currentBuild.description = isPrOpenedEvent ? 'PR opened' : 'PR comment /ai-review (open PR only)'
        }
      }
    }


    stage('Run AI review') {
      steps {
          script {
              def body = [
                  owner: env.REPO_OWNER,
                  pull_number: env.PR_NUMBER,
                  repo: env.REPO_NAME
              ]

              def response = httpRequest(
                  acceptType: 'APPLICATION_JSON',
                  contentType: 'APPLICATION_JSON',
                  httpMode: 'POST',
                  url: env.REVIEW_API_URL,
                  requestBody: groovy.json.JsonOutput.toJson(body),
              )

              echo "Status: ${response.status}"
              echo "Content: ${response.content}"
          }


        }
      }
    }

  post {
    always {
      archiveArtifacts artifacts: 'review.json', allowEmptyArchive: true
    }
  }
}
