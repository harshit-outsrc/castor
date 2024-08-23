#!/bin/groovy
pipeline {
    agent any
    options {
        skipStagesAfterUnstable()
        buildDiscarder(logRotator(numToKeepStr: "5"))
    }
    stages {
        stage('Install Environment') {
            when {
                expression {
                fileExists('env/bin/activate') == false
                }
            }
            steps {
                sshagent (['calbright_github_2']) {
                    sh """
                    echo 'creating virtualenv...'
                    virtualenv env
                    . ./env/bin/activate
                   pip install -e .
                    """
                }
            }
        }
        stage('Lint') {
            steps {
                sh """
                echo 'Running Linting'
                chmod +x ./tools/lint.sh
                """
                sshagent (['calbright_github_2']) {
                    echo 'fetching remote stage for flake comparison'
                    sh """
                    git config --unset-all remote.origin.fetch
                    git config remote.origin.fetch '+refs/heads/*:refs/remotes/origin/*'
                    git fetch --all
                    git stash
                    git checkout stage
                    git checkout "${env.BRANCH_NAME}"
                    git config pull.rebase false
                    git pull
                    . ./env/bin/activate
                    ./tools/lint.sh -x flake8 -b stage
                    """
                    }
            }
        }
        stage('Unit Tests') {
            failFast true
            steps {
                sshagent (['calbright_github_2']) {                    
                    sh """
                    . ./env/bin/activate
                    export PYTHONPATH=${pwd()}; ./tools/start_tests.sh
                    """
                }
            }
            post {
                always {
                    cobertura coberturaReportFile: 'coverage.xml'
                }
            }
        }
        stage('Deploy') {
            when {
                anyOf {
                    branch 'stage'; branch 'prod';
                }
            }
            steps {
                script {
                    switch(env.BRANCH_NAME) {
                    case 'stage':
                        ENV = "stage"
                        CRON_TIME = "30"
                        AWS_ACCOUNT = "523292522460"
                        break;
                    case 'prod':
                        ENV = "prod"
                        CRON_TIME = "30"
                        AWS_ACCOUNT = "523292522460"
                        break;
                    }
                    withCredentials([aws(accessKeyVariable:'AWS_ACCESS_KEY_ID', credentialsId: 'AWS Credentials', secretKeyVariable: 'AWS_SECRET_ACCESS_KEY')]) {
                        echo 'Checking for file changes'
                        sshagent (['calbright_github_2']) {
                            nvm('v18.14.0') {
                            sh """
                            python3 -m pip install --upgrade pip

                            # Checking if csep ingestion lambda needs to be deployed
                            CHANGED=`git diff --name-only \$GIT_PREVIOUS_COMMIT \$GIT_COMMIT lambda_functions/event_system`
                            if [ ! -z "\$CHANGED" ]; then
                                echo "Changes detected. Deploying event_system lambda"
                                PROPUS=aws,api_handler,gsuite,geolocator,hubspot,slack,sql ENVIRONMENT=${ENV} ./lambda_functions/event_system/deploy.sh
                            fi
                            
                            # Checking if pace and progress automation needs to be deployed
                            CHANGED=`git diff --name-only \$GIT_PREVIOUS_COMMIT \$GIT_COMMIT jobs/pace_progress_automation`
                            # Also only deploying in production
                            if [ ! -z "\$CHANGED" ] && [ "${ENV}" = "prod" ] ; then
                                echo "Changes detected. Deploying pace_progress_automation"
                                PROPUS=aws,api_handler,gsuite,hubspot AWS_ACCOUNT=${AWS_ACCOUNT} ./jobs/pace_progress_automation/deploy.sh
                            fi

                            # Checking if Symplicity CSM needs to be deployed
                            CHANGED=`git diff --name-only \$GIT_PREVIOUS_COMMIT \$GIT_COMMIT jobs/symplicity_student_ingestion`
                            # Also only deploying in production
                            if [ ! -z "\$CHANGED" ] && [ "${ENV}" = "prod" ] ; then
                                echo "Changes detected. Deploying symplicity_student_ingestion"
                                PROPUS=aws,api_handler AWS_ACCOUNT=${AWS_ACCOUNT} ./jobs/symplicity_student_ingestion/deploy.sh
                            fi

                            # Checking if automated term creation needs to be deployed
                            CHANGED=`git diff --name-only \$GIT_PREVIOUS_COMMIT \$GIT_COMMIT jobs/automated_term_creation`
                            if [ ! -z "\$CHANGED" ]; then
                                echo "Changes detected. Deploying automated_term_creation"
                                ENVIRONMENT=${ENV} AWS_ACCOUNT=${AWS_ACCOUNT} ./jobs/automated_term_creation/deploy.sh
                            fi


                            # Checking if calbright trigger workflow lambda needs to be deployed
                            CHANGED=`git diff --name-only \$GIT_PREVIOUS_COMMIT \$GIT_COMMIT lambda_functions/calbright_trigger_workflow`
                            # Also only deploying in stage
                            if [ ! -z "\$CHANGED" ] && [ "${ENV}" = "stage" ] ; then
                                echo "Changes detected. Deploying calbright_trigger_workflow lambda"
                                PROPUS=aws,api_handler,anthology,sql ENVIRONMENT=${ENV} ./lambda_functions/calbright_trigger_workflow/deploy.sh
                            fi

                            # Checking if psql trigger handler lambda needs to be deployed
                            CHANGED=`git diff --name-only \$GIT_PREVIOUS_COMMIT \$GIT_COMMIT lambda_functions/psql_trigger_handler`
                            if [ ! -z "\$CHANGED" ]; then
                                echo "Changes detected. Deploying psql_trigger_handler lambda"
                                PROPUS=aws,api_handler,sql ENVIRONMENT=${ENV} ./lambda_functions/psql_trigger_handler/deploy.sh
                            fi

                            # Checking if seed data lambda needs to be deployed
                            CHANGED=`git diff --name-only \$GIT_PREVIOUS_COMMIT \$GIT_COMMIT lambda_functions/seed_data_updates`
                            if [ ! -z "\$CHANGED" ]; then
                                echo "Changes detected. Deploying seed data lambda"
                                PROPUS=aws,sql ./lambda_functions/seed_data_updates/deploy.sh
                            fi

                            # Checking if canvas events lambda needs to be deployed
                            CHANGED=`git diff --name-only \$GIT_PREVIOUS_COMMIT \$GIT_COMMIT lambda_functions/canvas_events`
                            if [ ! -z "\$CHANGED" ]; then
                                echo "Changes detected. Deploying canvas_events lambda"
                                PROPUS=aws,api_handler,sql ENVIRONMENT=${ENV} ./lambda_functions/canvas_events/deploy.sh
                            fi

                            # Checking if Student Verification Job needs to be deployed
                            CHANGED=`git diff --name-only \$GIT_PREVIOUS_COMMIT \$GIT_COMMIT jobs/verify_student_accounts`
                            # Also only deploying in production
                            if [ ! -z "\$CHANGED" ] && [ "${ENV}" = "prod" ] ; then
                                echo "Changes detected. Deploying Student Acount Verifification Job"
                                PROPUS=aws,api_handler,gsuite AWS_ACCOUNT=${AWS_ACCOUNT} ./jobs/verify_student_accounts/deploy.sh
                            fi
                            """
                            }
                        }
                    }
                }
            }
        }

    }
    post {
      always {
        cleanWs()
      }
    }
}