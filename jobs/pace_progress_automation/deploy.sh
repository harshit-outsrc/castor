aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com
DOCKER_BUILDKIT=1 docker build --no-cache --ssh default -t pace_progress_automation:latest ./jobs/pace_progress_automation/

docker tag pace_progress_automation:latest $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/pace_progress_automation:latest
docker tag pace_progress_automation:latest $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/pace_progress_automation:build_$BUILD_ID

docker push $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/pace_progress_automation:latest
docker push $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/pace_progress_automation:build_$BUILD_ID

docker rmi pace_progress_automation:latest
docker rmi $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/pace_progress_automation:latest
docker rmi $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/pace_progress_automation:build_$BUILD_ID