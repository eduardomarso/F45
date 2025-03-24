git clone https://github.com/eduardomarso/F45.git
cd F45
docker build -t f45 .
docker tag f45:latest 825765390130.dkr.ecr.us-east-1.amazonaws.com/f45:latest
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 825765390130.dkr.ecr.us-east-1.amazonaws.com
docker push 825765390130.dkr.ecr.us-east-1.amazonaws.com/f45:latest

