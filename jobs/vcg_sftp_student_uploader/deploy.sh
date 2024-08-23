aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com
DOCKER_BUILDKIT=1 docker build --no-cache --ssh default -t vcg_sftp_student_uploader:latest ./jobs/vcg_sftp_student_uploader/

docker tag vcg_sftp_student_uploader:latest $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/vcg_sftp_student_uploader:latest
docker tag vcg_sftp_student_uploader:latest $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/vcg_sftp_student_uploader:build_$BUILD_ID

docker push $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/vcg_sftp_student_uploader:latest
docker push $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/vcg_sftp_student_uploader:build_$BUILD_ID

docker rmi vcg_sftp_student_uploader:latest
docker rmi $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/vcg_sftp_student_uploader:latest
docker rmi $AWS_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/vcg_sftp_student_uploader:build_$BUILD_ID