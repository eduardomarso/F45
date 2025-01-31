docker build -t video-splitter .
docker build -t video-splitter .docker run --rm \
  -v /Users/3dy/Downloads/Videos:/input \
  -v "/Users/3dy/Downloads/Splitted Videos":/output \
  video-splitter