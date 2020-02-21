#!/bin/bash
platform="Linux"
uname=$(uname)
case $uname in
	"Darwin")
	platform="MacOS / OSX"
	;;
	MINGW*)
	platform="Windows"
	;;
esac

run(){
	echo $1
	eval $1
}

display_help() {
	echo "Usage: $0 [options] {start|stop|rebuild|update|remove}" >&2
	echo
	echo "   start                Start DVM"
	echo "   stop                 Stop DVM"
	echo "   rebuild              Rebuild the Docker image if changes where made to the code"
    	echo "   update               Get the latest version of DVM from github"
	echo "   remove               Remove Docker images and volumes belonging to DVM"
	echo
	echo "   --dev                Run DVM in development mode"
	echo "   -h, --help           Show this help message"
}

create_data_dir(){
	if [[ $platform != "Windows" ]]; then
		run "mkdir -p data"
	fi
}

user_in_group(){
	groups $USER | grep &>/dev/null "\bdocker\b"
}

add_sudo(){
	local sudo_cmd="$1"
	if [[ $platform = "Linux" ]]; then
		if [[ ! user_in_group ]]; then
			sudo_cmd="sudo $1"
		fi
	fi
	echo "$sudo_cmd"
}

get_docker_compose(){
	local docker_compose="docker-compose -f docker-compose.yml"
	if [[ $platform = "Windows" ]]; then
		docker_compose="docker-compose -f docker-compose.windows.yml"
	fi
	docker_compose="$(add_sudo "$docker_compose")"
	echo "$docker_compose"
}

get_docker_image_rm(){
	local docker_rm_image="docker image rm  python:3.6 redis:alpine dvm dvm_worker"
	docker_rm_image="$(add_sudo "$docker_rm_image")"
	echo "$docker_rm_image"
}

get_docker_volume_rm(){
	local docker_rm_volume="docker volume rm dvm_appmedia"
	docker_rm_volume="$(add_sudo "$docker_rm_volume")"
	echo "$docker_rm_volume"
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
	run "$docker_compose down"
}

rebuild(){
	echo "Rebuilding DVM docker image"
	local docker_compose="$(get_docker_compose)"
	run "$docker_compose build"
}

update(){
	stop
	echo "Updating DVM"
	run "git pull origin master"
	echo "You can start DVM now"
}

remove(){
	stop
	echo "Removing docker image"
	local docker_rm_image="$(get_docker_image_rm)"
	run "$docker_rm_image"
	if [[ $platform = "Windows" ]]; then
		echo "Removing docker volume"
		local docker_rm_volume="$(get_docker_volume_rm)"
		run "$docker_rm_volume"
	fi
	echo "Removed docker content DVM directory can now be removed"
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
	rebuild)
		rebuild
		;;
	update)
		update
		;;
	remove)
		remove
		;;
	*)
		echo "Error: Unknown argument: $1" >&2
		display_help
		exit 1
esac
