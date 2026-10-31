// CSC418 Assignment 2 - Part II pipeline
// Plugins used: Git, Pipeline, Docker Pipeline, GitHub (webhook), Email Extension
pipeline {
    agent any

    options {
        skipDefaultCheckout(true)   // we check out with the Git plugin below
        timeout(time: 10, unit: 'MINUTES')
    }

    triggers {
        githubPush()                // runs on every GitHub push (webhook)
    }

    environment {
        REPO_URL     = 'https://github.com/ahmad120-com/devops-assignment2.git'
        COMPOSE_FILE = 'part2/docker-compose.yml'
        PROJECT      = 'part2'
        // CHANGE THIS to your EC2 Elastic IP
        APP_URL      = 'http://YOUR-ELASTIC-IP:9090'
    }

    stages {
        stage('Fetch code from GitHub') {
            steps {
                git branch: 'main', url: "${REPO_URL}"
            }
        }

        stage('Check code in a container') {
            steps {
                script {
                    // Docker Pipeline plugin: run steps inside a throwaway container
                    docker.image('python:3.11-slim').inside {
                        sh '''
                            python -m venv /tmp/venv
                            /tmp/venv/bin/pip install --no-cache-dir -q -r app/requirements.txt
                            PYTHONPYCACHEPREFIX=/tmp/pyc /tmp/venv/bin/python -m py_compile app/app.py
                            echo "Code check passed"
                        '''
                    }
                }
            }
        }

        stage('Build & start containers') {
            steps {
                sh "docker compose -p ${PROJECT} -f ${COMPOSE_FILE} down --remove-orphans || true"
                sh "docker compose -p ${PROJECT} -f ${COMPOSE_FILE} up -d"
            }
        }

        stage('Wait until app is up') {
            steps {
                sh '''
                    for i in $(seq 1 30); do
                        if curl -fs http://localhost:9090/health; then
                            echo ""; echo "App is up"; exit 0
                        fi
                        echo "Not ready yet ($i/30)..."; sleep 5
                    done
                    docker compose -p part2 -f part2/docker-compose.yml logs --tail=50
                    exit 1
                '''
            }
        }
    }

    post {
        always {
            script {
                def author = sh(script: "git log -1 --pretty=format:'%ae'", returnStdout: true).trim()
                def name   = sh(script: "git log -1 --pretty=format:'%an'", returnStdout: true).trim()
                def commit = sh(script: "git log -1 --pretty=format:'%h - %s'", returnStdout: true).trim()

                emailext(
                    to: author,
                    subject: "Build ${currentBuild.currentResult}: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                    mimeType: 'text/html',
                    body: """
                        <p>Hi ${name},</p>
                        <p>Your push triggered a Jenkins build.</p>
                        <ul>
                          <li><b>Result:</b> ${currentBuild.currentResult}</li>
                          <li><b>Job:</b> ${env.JOB_NAME} #${env.BUILD_NUMBER}</li>
                          <li><b>Commit:</b> ${commit}</li>
                          <li><b>Duration:</b> ${currentBuild.durationString}</li>
                          <li><b>Build log:</b> <a href="${env.BUILD_URL}console">${env.BUILD_URL}console</a></li>
                          <li><b>Application:</b> <a href="${APP_URL}">${APP_URL}</a></li>
                        </ul>
                    """
                )
            }
        }
    }
}
