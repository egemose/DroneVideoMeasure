# Howto - Push new version to docker hub

When a new version is ready to be pushed to dockerhub.com, the following commands should be used.
```
./dvm.sh build
docker tag dronevideomeasure-webapp:latest midtiby/dronevideomeasure_webapp
docker login -u "midtiby"
docker push midtiby/dronevideomeasure_webapp
```

To launch the program based on the images on dockerhub.com, use these commands.
```
docker compose -f ./dvm_runner/docker-compose.yml pull
docker compose -f ./dvm_runner/docker-compose.yml up
```
