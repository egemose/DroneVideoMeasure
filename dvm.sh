#!/bin/bash
platform="Linux" # Assumed
uname=$(uname)
case $uname in
	"Darwin")
	platform="MacOS / OSX"
	;;
	MINGW*)
	platform="Windows"
	;;
esac

if [[ $platform = "Linux" ]]; then
	eval "mkdir -p data"
	if groups $USER | grep &>/dev/null '\bdocker\b'; then
		echo "User in docker group. no need for sudo"
		command="docker-compose -f docker-compose.yml"
	else
		echo "User not in docker group. Using sudo!"
		command="sudo docker-compose -f docker-compose.yml"
	fi
elif [[ $platform = "MacOS / OSX" ]]; then
	eval "mkdir -p data"
	command="docker-compose -f docker-compose.yml"
elif [[ $platform = "Windows" ]]; then
	command="docker-compose -f docker-compose.windows.yml"
fi

if [[ $1 = "start" ]]; then
	command="$command up"
elif [[ $1 = "stop" ]]; then
	command="$command down"
elif [[ $1 = "rebuild" ]]; then
	command="$command build"
fi

eval "$command"
