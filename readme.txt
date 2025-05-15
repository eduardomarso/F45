git clone https://github.com/ezodis/F45.git
cd F45
rm -rf .git
rm -rf readme.txt
docker build -t f45 .
docker run --rm \
  -v "$(pwd)/Input":/app/input \
  -v "$(pwd)/Output":/app/output \
  f45
