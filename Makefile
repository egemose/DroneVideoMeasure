push_images_to_docker:
	docker tag dronevideomeasure_worker:latest midtiby/dronevideomeasure_worker:latest 
	docker tag dronevideomeasure_webapp:latest midtiby/dronevideomeasure_webapp:latest 
	docker push midtiby/dronevideomeasure_webapp:latest
	docker push midtiby/dronevideomeasure_worker:latest
