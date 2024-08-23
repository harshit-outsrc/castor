aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com
DOCKER_BUILDKIT=1 docker build --no-cache --ssh default -t automated_term_creation:latest ./jobs/automated_term_creation/

docker tag automated_term_creation:latest $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/automated_term_creation_$ENVIRONMENT:latest
docker tag automated_term_creation:latest $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/automated_term_creation_$ENVIRONMENT:build_$BUILD_ID

docker push $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/automated_term_creation_$ENVIRONMENT:latest
docker push $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/automated_term_creation_$ENVIRONMENT:build_$BUILD_ID

docker rmi automated_term_creation:latest
docker rmi $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/automated_term_creation_$ENVIRONMENT:latest
docker rmi $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/automated_term_creation_$ENVIRONMENT:build_$BUILD_ID