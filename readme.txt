docker build -t f45 .


docker run --rm \
  -v "$(pwd)/input/workout":/input/workout \
  -v "$(pwd)/Videos/📝":/input/📝 \
  -v "$(pwd)/Output":/output \
f45
