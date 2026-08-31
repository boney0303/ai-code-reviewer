import java.util.Date
import java.text.SimpleDateFormat
@Library('shared-pipeline-library') _

pipeline {
    agent {label 'linux'}
    options {
        timeout(time: 1, unit: 'HOURS')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }
    parameters {
        booleanParam(
            defaultValue: false,
            description: 'Build a docker image upon completion',
            name: 'buildImage'
        )
        booleanParam(
            defaultValue: false,
            description: 'Deploy helm chart upon completion',
            name: 'deployHelm'
        )
        choice(
            name: 'buildLocation',
            choices: ['integration'], 
            description: 'Repo to deploy image towards')

        
        booleanParam(name: 'DRY_RUN', defaultValue: false, description: 'Show changes without applying them')
        string(name: 'ORG', defaultValue: 'example-org', description: 'GitHub organization name')
        string(name: 'INSTALLATION_ID', defaultValue: '000000', description: 'GitHub App installation ID')
        string(name: 'CONFIG_FILE', defaultValue: 'repo-sync.yml', description: 'YAML file path')

    }
    environment {
        REG_CREDS = 'container-registry-credentials'
        registry = 'example-org/ai-code-reviewer'
        integrationRepo = 'https://registry.example.com/'
        projectName = 'AI-CODE-REVIEWER'
        maintainer = "platform-team@example.com"
        version = ''
        artifactId = ''
        DOCKER_TAG = '' 
        DOCKER_LABELS = ''
        HELM_CHART = './helm_chart'
        HELM_RELEASE_PROD = 'ai-code-reviewer'
        HELM_NS_PROD = 'ai-code-reviewer'
        HELM_VALUES_PROD = './helm_chart/values.yaml'
        BUILD_IMAGE = false
        HELM_DEPLOY = false
        GHE_API   = 'https://github.example.com/api/v3'
        GITHUB_TOKEN = credentials('github-api-token')

    }
    stages {
        stage("Cloning repository"){
            steps{
                checkout scm
            }
        }

        stage('Sync GitHub App repos') {
            when {
                allOf {
                    branch 'main'
                    changeset "repo-sync.yml"
                }
            }
            steps {
                script {
                def repoSync = load 'repo-sync.groovy'
                repoSync.syncGitHubAppRepos(
                apiBaseUrl: env.GHE_API,
                org: params.ORG,
                installationId: params.INSTALLATION_ID,
                githubAppCredId: 'github-app-credentials',
                patCredId: 'github-api-token',
                configFile: 'repo-sync.yml',
                dryRun: params.DRY_RUN
                )
                }
            }
        }

        stage('Set Deploy Env') {
            steps {
                script {
                    BUILD_IMAGE = params.buildImage
                    HELM_DEPLOY = params.deployHelm
                    // Detect branch name
                    def branchName = env.BRANCH_NAME
                    // Go Ahead with continous deployment for dev environment
                    if (branchName == 'main') {
                        echo 'Setting buildImage to true'
                        BUILD_IMAGE = true
                        echo 'Setting helm deploy to true'
                        HELM_DEPLOY = true
                    } 
                    echo "Branch: ${branchName}"

                    if (HELM_DEPLOY && !BUILD_IMAGE) {
                        error "HELM_DEPLOY was set without an image build.  BUILD_IMAGE is a pre-req to deploy via helm"
                    }
                }
            }
        }

        stage('Gathering version') {
             when {
                anyOf{
                    expression { return BUILD_IMAGE }
                }
            }
            steps {
                echo 'Running verification stage'
                dir('') {
                    script {
                        version = sh(script: "cat ./helm_chart/Chart.yaml | grep appVersion | awk -F\": \" '{print \$2}' | tr -d '\"'", returnStdout: true).trim()
                        echo "Version: ${version}"
                    }
                }
                echo 'Finished verification stage'
            }
        }

        stage('Generating environment file') {
             when {
                anyOf{
                    expression { return BUILD_IMAGE }
                }
             }
            steps {
                echo 'Running environment file stage'
                dir('app') {
                    script {
                        withCredentials([file(credentialsId: 'ai_code_reviewer_env', variable: 'ai_code_reviewer_env')]) {
                            sh "pwd"
                            sh "ls -altrh"
                            sh "cp $ai_code_reviewer_env .env"
                            sh "chmod 777 .env"
                            sh "ls -altrh"
                        }
                    }
                }

                echo 'Finished environment file stage'
            }
        }
        
        stage('Building an Image'){
             when {
                anyOf{
                    expression { return BUILD_IMAGE }
                }
             }
            steps {
                    script {
                        def cleanedVersion = version.split('-')[0].trim()
                        def isoDateTimeUTCTZFormat = new SimpleDateFormat("yyyyMMdd'T'HHmmss'Z'")
                        isoDateTimeUTCTZFormat.setTimeZone(TimeZone.getTimeZone("UTC"))
                        def buildDate = isoDateTimeUTCTZFormat.format(new Date())

                        DOCKER_TAG = "${cleanedVersion}-${buildDate}"
                        DOCKER_LABELS = "--label org.opencontainers.image.version=${cleanedVersion} " +
                                            "--label org.opencontainers.image.created=${buildDate} " +
                                            "--label org.opencontainers.image.revision=${env.GIT_COMMIT} " +
                                            "--label org.opencontainers.image.source=${env.GIT_URL} " +
                                            "--label org.opencontainers.image.title=${projectName} " +
                                            "--label org.opencontainers.image.authors=${maintainer} "

                        echo "Docker Tag ${DOCKER_TAG}"

                        echo "Docker Labels: ${DOCKER_LABELS}"

                        echo "Logging into registry: ${integrationRepo}"
                        docker.withRegistry("${integrationRepo}", "${REG_CREDS}") {
                            echo "Building image"
                            def dockerImage = docker.build("${registry}:${DOCKER_TAG}", "${DOCKER_LABELS} .")
                            echo "Pushing image"
                            dockerImage.push()
                            
                            echo 'Cleanup Docker Image'
                            sh  """#!/bin/bash
                                    docker images | grep '${DOCKER_TAG}' | awk '{print \$3}' | sort -u | xargs docker rmi -f
                                    exit 0
                                """
                            echo "End of Build"
                        }
                    }
                
            }
        }

        stage('Deploying via helm'){
          when{
                allOf{
                    expression { return HELM_DEPLOY }
                    expression{ return BUILD_IMAGE }
                }
            }
            stages{
                stage('Running helm lint, template and Deploy'){
                    when{
                        allOf{
                            expression { return HELM_DEPLOY }
                            expression{ return BUILD_IMAGE }
                        }
                    }
                    steps{
                        script{
                            withCredentials([usernamePassword(credentialsId: env.REG_CREDS, usernameVariable: 'REG_USER', passwordVariable: 'REG_TOKEN'  )]){
                                def release_name = ''
                                def ns = ''
                                def valuesfile = ''
                                def config = [:]
                                echo "Image Tag: ${DOCKER_TAG}"
                                env.IMAGE_PASSWORD = REG_TOKEN

                                release_name = env.HELM_RELEASE_PROD
                                ns = env.HELM_NS_PROD
                                valuesfile = env.HELM_VALUES_PROD

                                config = [
                                    name: release_name,
                                    chart: HELM_CHART,
                                    namespace: ns,
                                    debug: false,
                                    installIfNotExists: true,
                                    atomic: true,
                                    dryRun: false,
                                    values:[
                                        'api.containerLabel': DOCKER_TAG,
                                        debug: true,
                                    ],
                                    valuesFiles:[
                                        valuesfile,
                                    ]
                                ]
                                def lintResult = helmUtils.validateChart(config, this)
                                if (lintResult.exitCode == 0) {
                                    echo "${lintResult.output}"
                                    echo "✅ Chart validation passed"
                                } else {
                                    error "❌ Chart validation failed"
                                }

                                echo ("Running helm template")
                                def templateResult = helmUtils.template(config,this)
                                if (templateResult.exitCode == 0 ) {
                                    echo "✅ Helm templating succeeded"
                                }else{
                                    error ("❌ Unable to template chart")
                                }

                                echo "Running helm upgrade"
                                 def deployResult = helmUtils.upgradeChart(config, this)
                                if (deployResult.exitCode == 0) {
                                    echo "✅ Helm deploy succeeded"
                                }else {
                                    error ("❌ Helm deploy failed")
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    post{
     always{
        cleanWs()
      }
    }
}
