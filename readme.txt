docker build -t video-splitter .
docker run --rm -v "$(pwd)/Videos":/input -v "$(pwd)/Output":/output video-splitter
