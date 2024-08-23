aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com
DOCKER_BUILDKIT=1 docker build --no-cache --ssh default -t verify_student_accounts:latest ./jobs/verify_student_accounts/

docker tag verify_student_accounts:latest $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/verify_student_accounts:latest
docker tag verify_student_accounts:latest $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/verify_student_accounts:build_$BUILD_ID

docker push $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/verify_student_accounts:latest
docker push $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/verify_student_accounts:build_$BUILD_ID

docker rmi verify_student_accounts:latest
docker rmi $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/verify_student_accounts:latest
docker rmi $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/verify_student_accounts:build_$BUILD_ID