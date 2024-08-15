# Howto - Get terminal access to docker container

When working on the application it can sometimes be beneficial to
log on to one of the running containers to obtain access to a shell. 
This can be done as follows.
```
docker ps
docker exec -it dvm_app bash
```
