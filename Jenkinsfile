pipeline {
    agent any

    options {
        disableConcurrentBuilds()
    }

    parameters {
        choice(
            name: 'VERSION',
            choices: ['v1', 'v2'],
            description: 'Select application version to deploy'
        )
    }

    environment {
        APP_NAME = 'release-app'
        KUBECONFIG = '/var/lib/jenkins/.kube/config'
        HOME = '/var/lib/jenkins'
        MINIKUBE_HOME = '/var/lib/jenkins'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    docker build \
                      --build-arg APP_VERSION=${VERSION} \
                      -t ${APP_NAME}:${VERSION} .
                '''
            }
        }

        stage('Load Image into Minikube') {
            steps {
                sh '''
                    minikube image load ${APP_NAME}:${VERSION}
                '''
            }
        }

        stage('Deploy Selected Version') {
            steps {
                script {
                    def targetDeployment = params.VERSION == 'v1' ? 'release-v1' : 'release-v2'
                    def targetService = params.VERSION == 'v1' ? 'release-service' : 'release-v2-service'

                    withEnv([
                        "TARGET_DEPLOYMENT=${targetDeployment}",
                        "TARGET_SERVICE=${targetService}",
                        "EXPECTED_VERSION=${params.VERSION}"
                    ]) {
                        try {
                            sh '''
                                kubectl set image deployment/${TARGET_DEPLOYMENT} \
                                  release-app=${APP_NAME}:${EXPECTED_VERSION} \
                                  --kubeconfig=${KUBECONFIG}

                                kubectl rollout status deployment/${TARGET_DEPLOYMENT} \
                                  --timeout=120s \
                                  --kubeconfig=${KUBECONFIG}
                            '''

                            sh '''
                                set -eu
                                PORT=18081

                                kubectl port-forward service/${TARGET_SERVICE} \
                                  ${PORT}:5000 \
                                  --address=127.0.0.1 \
                                  --kubeconfig=${KUBECONFIG} \
                                  >/tmp/release-port-forward.log 2>&1 &

                                PF_PID=$!
                                trap 'kill "$PF_PID" 2>/dev/null || true' EXIT

                                for i in $(seq 1 30); do
                                    response=$(curl -fsS http://127.0.0.1:${PORT}/health 2>/dev/null || true)

                                    if [ -n "$response" ]; then
                                        echo "$response"
                                        echo "$response" | grep -q "\\"status\\":\\"healthy\\""
                                        echo "$response" | grep -q "\\"version\\":\\"${EXPECTED_VERSION}\\""
                                        exit 0
                                    fi

                                    sleep 2
                                done

                                echo "Health check failed."
                                cat /tmp/release-port-forward.log || true
                                exit 1
                            '''

                            echo "Deployment and health check successful."

                        } catch (err) {
                            echo "Deployment failed. Rolling back ${targetDeployment}..."

                            sh '''
                                kubectl rollout undo deployment/${TARGET_DEPLOYMENT} \
                                  --kubeconfig=${KUBECONFIG}

                                kubectl rollout status deployment/${TARGET_DEPLOYMENT} \
                                  --timeout=120s \
                                  --kubeconfig=${KUBECONFIG}
                            '''

                            throw err
                        }
                    }
                }
            }
        }
    }

    post {
        success {
            echo "Release ${VERSION} deployed successfully."
        }

        failure {
            echo "Release failed. Check deployment and rollback logs."
        }
    }
}
