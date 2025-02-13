docker build -t f45 .


docker run --rm \
  -v "$(pwd)/Input/workout":/input/workout \
  -v "$(pwd)/Input/📝":/input/📝 \
  -v "$(pwd)/Output":/output \
f45
