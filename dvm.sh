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

command=""
if [[ $platform = "Linux" ]]; then
	eval "mkdir -p data"
	if groups $USER | grep &>/dev/null '\bdocker\b'; then
		echo "User in docker group. no need for sudo"
	else
		echo "User not in docker group. Using sudo!"
	    	command="$command sudo"
	fi
fi

if [[ $platform = "Windows" ]]; then
	command="$command docker-compose -f docker-compose.windows.yml"
else
	command="$command docker-compose -f docker-compose.yml"
fi

if [[ $1 = "start" ]]; then
	command="$command up"
elif [[ $1 = "stop" ]]; then
	command="$command down"
elif [[ $1 = "rebuild" ]]; then
	command="$command build"
fi

eval "$command"
