docker build -t f45 .
docker run -d --rm \
  -v "$(pwd)/Input/workout":/app/input/workout \
  -v "$(pwd)/Input/transcript":/app/input/transcript \
  -v "$(pwd)/Output":/app/output \
  f45
