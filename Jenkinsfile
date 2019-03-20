pipeline {
    agent any
    environment {
        OS_TEST_PATH = "$WORKSPACE/tests/functional"
        OS_LOG_PATH = "$WORKSPACE/.logs"
    }
    stages {
        stage('poppy_venv') {
            steps {
                slackSend (color: '#ffe100', message: "STARTED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})")
                echo "Setup poppy_venv and install deps"
                sh 'if [ -d poppy_venv/ ]; then rm -rf poppy_venv; fi'
                sh 'if [ -d ~/base_poppy_venv ]; then virtualenv-clone ~/base_poppy_venv poppy_venv; else virtualenv poppy_venv; fi'
                sh '''. poppy_venv/bin/activate && if [ $(pip -V | awk '{print $2}') != "9.0.3" ]; then curl -s https://bootstrap.pypa.io/get-pip.py | python - "pip==9.0.3"; fi'''
                sh '. poppy_venv/bin/activate && pip install --find-links=~/wheels -U wheel'
                sh '. poppy_venv/bin/activate && pip install --find-links=~/wheels setuptools==35.0.2'
                sh '. poppy_venv/bin/activate && pip install --find-links=~/wheels pbr==0.11.0 certifi==2018.11.29 testrepository'
                sh '. poppy_venv/bin/activate && pip install --find-links=~/wheels -r requirements/requirements.txt'
                sh 'if [ ! -d ~/base_poppy_venv ]; then virtualenv-clone poppy_venv ~/base_poppy_venv; fi'
            }
        }
        stage('poppy_tests_venv') {
            steps {
                echo "Setup poppy_tests_venv and install deps"
                sh 'if [ -d poppy_tests_venv/ ]; then rm -rf poppy_tests_venv; fi'
                sh 'if [ -d ~/base_poppy_tests_venv ]; then virtualenv-clone ~/base_poppy_tests_venv poppy_tests_venv; else virtualenv-clone poppy_venv poppy_tests_venv; fi'
                sh '. poppy_tests_venv/bin/activate && pip install --find-links=~/wheels -r tests/test-requirements.txt'
                sh 'if [ ! -d ~/base_poppy_tests_venv ]; then virtualenv-clone poppy_tests_venv ~/base_poppy_tests_venv; fi'
                sh '. poppy_tests_venv/bin/activate && python setup.py install'
            }
        }
        stage('Run Tests') {
            parallel {
                stage('PyLint') {
                    steps {
                        sh '''
                        echo "Pylint tests are temporarily disabled"
                        #. poppy_tests_venv/bin/activate
                        # pycodestyle --max-line-length=119 --statistics --first
                        '''
                    }
                }
                stage('Unit') {
                    steps {
                        sh '''
                        echo "Unit tests are temporarily disabled"
                        #. poppy_tests_venv/bin/activate
                        #nosetests --with-coverage --cover-package=poppy --with-xunit --xunit-file=unit-tests.xml tests/unit
                        '''
                    }
                    post {
                        always {
                            echo "junit 'unit-tests.xml' is currently disabled"
                        }
                    }
                }
                stage('Functional') {
                    steps {
                        sh '''
                        echo "Functional tests are temporarily disabled"
                        #. poppy_tests_venv/bin/activate
                        #nosetests --with-coverage --cover-package=poppy --with-xunit --xunit-file=functional-tests.xml tests/functional
                        '''
                    }
                    post {
                        always {
                            echo "junit 'functional-tests.xml' is currently disabled"
                        }
                    }

                }
            }
        }
        stage('Build-and-Upload') {
            parallel {
                stage('PyPI Preview') {
                    when { anyOf { branch 'pre-release'; branch 'release' } }
                    steps {
                        sh '''
                        echo "Build and Upload PREVIEW Wheel for $BRANCH_NAME"
                        . poppy_venv/bin/activate
                        rm -rf dist
                        PBR_VERSION=2019.2.${BUILD_NUMBER} python setup.py bdist_wheel upload -v -r prev
                        '''
                    }
                }
                stage('PyPI Production') {
                    when { branch 'release' }
                    steps {
                        echo "want to use when tag regex here but it seems broken, using when branch for now"
                        sh '''
                        echo "Build and Upload PROD Wheel for $TAG_NAME - this is temporarily disabled"
                        . poppy_venv/bin/activate
                        rm -rf dist
                        PBR_VERSION=2019.2.${BUILD_NUMBER} python setup.py bdist_wheel upload -v -r prod
                        '''
                    }
                }
            }
        }
        stage('Deploy Prev IAD') {
            when { anyOf { branch 'pre-release'; branch 'release' } }
            parallel {
                stage('pwkr?a-ccv-iad') {
                    steps {
                        sh 'ssh jenkins@salt-test.altcdn.com  "bash preview-deploy-pwkr.sh"'
                    }
                }
                stage('cdn?a-ccv-iad') {
                    steps {
                        sh 'ssh jenkins@salt-test.altcdn.com  "bash preview-deploy-cdn.sh"'
                    }
                }
            }
        }
        stage('Prev API Check') {
            when { anyOf { branch 'pre-release'; branch 'release' } }
            steps {
                sh 'sleep 5'
                sh 'nc -zv preview.cdn.api.rackspacecloud.com 443'
            }
        }
        stage('Deploy Prod HKG') {
            when {
                beforeInput true
                branch 'release'
            }
            input {

                message "Should we deploy to Prod HKG?"
                ok "Register HKG Choice"
                parameters {
                    string(name: 'DEPLOY_HKG', defaultValue: 'FALSE', description: 'Enter TRUE to deploy, leave FALSE to skip.')
                }
            }
            steps {
                echo "Create backup of poppy installation and config"
                sh '''
                    if [ $DEPLOY_HKG = "TRUE" ]; then
                        ssh jenkins@104.130.7.18 'sudo salt -v pwkr?a-ccp-hkg cmd.run "bash backup_poppy.sh"'
                        ssh jenkins@104.130.7.18 'sudo salt -v cdn?a-ccp-hkg cmd.run "bash backup_poppy.sh"'
                    fi
                '''
                echo "start deploy poppy workers"
                sh '''
                    if [ $DEPLOY_HKG = "TRUE" ]; then
                        ssh jenkins@104.130.7.18 'sudo salt -v pwkr?a-ccp-hkg state.sls poppy_worker cdn-prod-hkg test=True'
                    fi
                '''
                echo "start deploy poppy servers"
                sh '''
                    if [ $DEPLOY_HKG = "TRUE" ]; then
                        ssh jenkins@104.130.7.18 'sudo salt -v cdn?a-ccp-hkg state.sls poppy_server cdn-prod-hkg test=True'
                    fi
                '''
            }
        }
        stage('Deploy Prod LON') {
            when {
                beforeInput true
                branch 'release'
            }
            input {
                message "Should we deploy to Prod LON?"
                ok "Register LON Choice"
                parameters {
                    string(name: 'DEPLOY_LON', defaultValue: 'FALSE', description: 'Enter TRUE to deploy, leave FALSE to skip.')
                }
            }
            steps {
                echo "Create backup of poppy installation and config"
                sh '''
                    if [ $DEPLOY_LON = "TRUE" ]; then
                        ssh jenkins@104.130.7.18 'sudo salt -v pwkr?a-ccp-lon cmd.run "bash backup_poppy.sh"'
                        ssh jenkins@104.130.7.18 'sudo salt -v cdn?a-ccp-lon cmd.run "bash backup_poppy.sh"'
                    fi
                '''
                echo "start deploy poppy workers"
                sh '''
                    if [ $DEPLOY_LON = "TRUE" ]; then
                        ssh jenkins@104.130.7.18 'sudo salt -v pwkr?a-ccp-lon state.sls poppy_worker cdn-prod-lon test=True'
                    fi
                '''
                echo "start deploy poppy servers"
                sh '''
                    if [ $DEPLOY_LON = "TRUE" ]; then
                        ssh jenkins@104.130.7.18 'sudo salt -v cdn?a-ccp-lon state.sls poppy_server cdn-prod-lon test=True'
                    fi
                '''
            }
        }
        stage('Deploy Prod IAD') {
            when {
                beforeInput true
                branch 'release'
            }
            input {
                message "Should we deploy to Prod IAD?"
                ok "Register IAD Choice"
                parameters {
                    string(name: 'DEPLOY_IAD', defaultValue: 'FALSE', description: 'Enter TRUE to deploy, leave FALSE to skip.')
                }
            }
            steps {
                echo "Create backup of poppy installation and config"
                sh '''
                    if [ $DEPLOY_IAD = "TRUE" ]; then
                        ssh jenkins@104.130.7.18 'sudo salt -v pwkr?a-ccp-iad cmd.run "bash backup_poppy.sh"'
                        ssh jenkins@104.130.7.18 'sudo salt -v cdn?a-ccp-iad cmd.run "bash backup_poppy.sh"'
                    fi
                '''
                echo "start deploy poppy workers"
                sh '''
                    if [ $DEPLOY_IAD = "TRUE" ]; then
                        ssh jenkins@104.130.7.18 'sudo salt -v pwkr?a-ccp-iad state.sls poppy_worker cdn-prod-iad test=True'
                    fi
                '''
                echo "start deploy poppy servers"
                sh '''
                    if [ $DEPLOY_IAD = "TRUE" ]; then
                        ssh jenkins@104.130.7.18 'sudo salt -v cdn?a-ccp-iad state.sls poppy_server cdn-prod-iad test=True'
                    fi
                '''
            }
        }
        stage('Prod API Check') {
            parallel {
                stage('Prod Global') {
                    when { branch 'release' }
                    steps {
                        sh 'sleep 5'
                        sh 'nc -zv global.cdn.api.rackspacecloud.com 443'
                    }
                }
                stage('Prod HKG LB') {
                    when { branch 'release' }
                    steps {
                        sh 'sleep 5'
                        sh 'nc -zv 119.9.70.202 443'
                    }
                }
                stage('Prod LON LB') {
                    when { branch 'release' }
                    steps {
                        sh 'sleep 5'
                        sh 'nc -zv 134.213.79.89 443'
                    }
                }
                stage('Prod IAD LB') {
                    when { branch 'release' }
                    steps {
                        sh 'sleep 5'
                        sh 'nc -zv 23.253.146.253 443'
                    }
                }
            }
        }
        stage('Finish') {
            steps {
                echo "End of pipeline reached."
            }
        }
    }
    post {
        success {
            slackSend (color: '#008902', message: "SUCCESSFUL: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})")
        }
        failure {
            slackSend (color: '#FF0000', message: "FAILED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})")
        }
    }
}
