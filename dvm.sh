#!/bin/bash

run(){
	echo $1
	eval $1
}

display_help() {
	echo "Usage: $0 [options] {start|stop|build|update|shell|remove}" >&2
	echo
	echo "   start                Start DVM"
	echo "   stop                 Stop DVM"
	echo "   build                Rebuild the Docker image if changes where made to the code"
	echo "   shell                Start a bash shell inside the docker container"
	echo
	echo "   --dev                Run DVM in development mode"
	echo "   -h, --help           Show this help message"
}

create_data_dir(){
	run "mkdir -p data"
}

get_docker_compose(){
	local docker_compose="docker compose -f docker-compose.yml"
	echo "$docker_compose"
}

start(){
	if [[ $dev_mode = true ]]; then
		echo "Starting DVM in development mode..."
	else
		echo "Starting DVM"
	fi
	create_data_dir
	local docker_compose="$(get_docker_compose)"
	if [[ $dev_mode = true ]]; then
		docker_compose="$docker_compose -f docker-compose-dev.yml"
	fi
	docker_compose="$docker_compose up"
	if [[ $attach != true ]] && [[ $dev_mode != true ]]; then
		docker_compose="$docker_compose -d"
	fi
	run "$docker_compose"
}

stop(){
	echo "Stopping DVM"
	local docker_compose="$(get_docker_compose)"
	docker_compose="$docker_compose -f docker-compose-dev.yml"
	run "$docker_compose down"
}

build(){
	echo "Rebuilding DVM docker image"
	local docker_compose="$(get_docker_compose)"
	docker_compose="$docker_compose -f docker-compose-dev.yml"
	run "$docker_compose build"
}

shell(){
	local docker_compose="$(get_docker_compose)"
	if [[ $dev_mode = true ]]; then
		docker_compose="$docker_compose -f docker-compose-dev.yml"
	fi
	docker_compose="$docker_compose run webapp /bin/bash"
	run "$docker_compose"
}

POSITIONAL=()
while [[ $# -gt 0 ]]
do
	case "$1" in
		--dev)
			echo "devmode"
			dev_mode=true
			shift # past argument
	    		;;
		--attach)
			echo "Attaching to the docker containers"
			attach=true
			shift # past argument
			;;
		-h | --help)
			display_help
			exit 0
			;;
		-*)
			echo "Error: Unknown option: $1" >&2
			display_help
			exit 1
			;;
		*)    # unknown option
			POSITIONAL+=("$1") # save it in an array for later
		  	shift # past argument
		  	;;
	esac
done
set -- "${POSITIONAL[@]}" # restore positional parameter

case "$1" in
	start)
		start
		;;
	stop)
		stop
		;;
	build)
		build
		;;
	shell)
		shell
		;;
	*)
		echo "Error: Unknown argument: $1" >&2
		display_help
		exit 1
esac
