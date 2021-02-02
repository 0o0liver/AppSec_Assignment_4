# Spell Checking Web Application
Travis Build Status: [![Build Status](https://travis-ci.org/0o0liver/AppSec_Assignment_4.svg?branch=master)](https://travis-ci.org/0o0liver/AppSec_Assignment_4)
## Deploy using public Docker Image
The Docker Image of this application is published on Docker Hub, it can be accessed at [0o0riley/spell-check](https://hub.docker.com/repository/docker/0o0riley/spell-check). There are three tags for this image, both ```for_k8s``` and ```signed``` are signed tags, it is suggested to use either one of these two tags. However, all tags are generated from the same root image. To deploy the spell check service, be sure to create a ```Docker Secret``` called ```secret_key```. Command for deploying is 
```
docker run -p 8080:5000 0o0riley/spell-check:signed 
```
Service then can be accessed through port 8080.
## Deploy using Github source code
Before deploying the service, be sure to replace the secret key content in ```root_secret_key.txt```. The spell check service can be deployed using command
```
docker-compose up -d
```
Service then can be accessed through port 8080.
## Deploy using Kubernetes
This service can also be deployed using Kubernetes, with Kubernetes Secret. Before deploying, be sure to replace the content of ```root_key``` field in [```/KubernetesConfig/secret.yaml```](https://github.com/0o0liver/AppSec_Assignment_4/blob/master/KubernetesConfig/secret.yaml). Command to deploy the service are
```
# create Kubernetes Secret
kubectl apply -f KubernetesConfig/secret.yaml
# create deployment
kubectl apply -f KubernetesConfig/deployment.yaml
# expose service
kubectl apply -f KubernetesConfig/service.yaml
```
Service then can be accessed through port 8080.
