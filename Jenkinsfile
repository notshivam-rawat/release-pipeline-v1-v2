
pipeline {
    agent any

    parameters {
        choice(
            name: 'VERSION',
            choices: ['v1', 'v2', 'v-fail'],
            description: 'Select application version to deploy'
        )
    }

    environment {
        APP_NAME = 'release-app'
        DEPLOYMENT = 'release-v1'
        KUBECONFIG = '/var/lib/jenkins/.kube/config'
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
                    if [ "$VERSION" != "v-fail" ]; then
                        minikube image load ${APP_NAME}:${VERSION}
                    fi
                '''
            }
        }

        stage('Deploy') {
            steps {
                script {
                    try {
                        def deployImage = params.VERSION == 'v-fail' ?
                            "${APP_NAME}:does-not-exist" :
                            "${APP_NAME}:${VERSION}"

                        sh """
                            kubectl set image deployment/${DEPLOYMENT} \
                              release-app=${deployImage} \
                              --kubeconfig=${KUBECONFIG}

                            kubectl rollout status deployment/${DEPLOYMENT} \
                              --timeout=120s \
                              --kubeconfig=${KUBECONFIG}
                        """

                        sh '''
                            kubectl port-forward service/release-service \
                              8081:5000 \
                              --kubeconfig=${KUBECONFIG} \
                              >/tmp/release-port-forward.log 2>&1 &

                            echo $! > /tmp/release-port-forward.pid

                            for i in $(seq 1 20); do
                                response=$(curl -fsS http://127.0.0.1:8081/health 2>/dev/null || true)

                                if [ -n "$response" ]; then
                                    echo "$response"
                                    echo "$response" | grep -q "\"version\":\"${VERSION}\"" || exit 1
                                    exit 0
                                fi

                                sleep 2
                            done

                            exit 1
                        '''

                        echo "Deployment and health check successful."

                    } catch (err) {
                        echo "Deployment failed. Rolling back..."

                        sh '''
                            kubectl rollout undo deployment/${DEPLOYMENT} \
                              --kubeconfig=${KUBECONFIG}

                            kubectl rollout status deployment/${DEPLOYMENT} \
                              --timeout=120s \
                              --kubeconfig=${KUBECONFIG}
                        '''

                        throw err

                    } finally {
                        sh '''
                            if [ -f /tmp/release-port-forward.pid ]; then
                                kill $(cat /tmp/release-port-forward.pid) || true
                                rm -f /tmp/release-port-forward.pid
                            fi
                        '''
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
