aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com
DOCKER_BUILDKIT=1 docker build --no-cache --ssh default -t strut_progress_activity_tracker:latest ./jobs/strut_progress_activity_tracker/

docker tag strut_progress_activity_tracker:latest $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/strut_progress_activity_tracker:latest
docker tag strut_progress_activity_tracker:latest $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/strut_progress_activity_tracker:build_$BUILD_ID

docker push $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/strut_progress_activity_tracker:latest
docker push $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/strut_progress_activity_tracker:build_$BUILD_ID

docker rmi strut_progress_activity_tracker:latest
docker rmi $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/strut_progress_activity_tracker:latest
docker rmi $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/strut_progress_activity_tracker:build_$BUILD_ID