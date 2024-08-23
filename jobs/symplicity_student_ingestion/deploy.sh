aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com
DOCKER_BUILDKIT=1 docker build --no-cache --ssh default -t symplicity_student_ingestion:latest ./jobs/symplicity_student_ingestion/

docker tag symplicity_student_ingestion:latest $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/symplicity_student_ingestion:latest
docker tag symplicity_student_ingestion:latest $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/symplicity_student_ingestion:build_$BUILD_ID

docker push $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/symplicity_student_ingestion:latest
docker push $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/symplicity_student_ingestion:build_$BUILD_ID

docker rmi symplicity_student_ingestion:latest
docker rmi $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/symplicity_student_ingestion:latest
docker rmi $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/symplicity_student_ingestion:build_$BUILD_ID