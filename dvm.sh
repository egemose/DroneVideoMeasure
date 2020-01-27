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

if [[ $platform = "Windows" ]]; then
	command="docker-compose -f docker-compose.windows.yml"
else
	command="mkdir -p data && docker-compose -f docker-compose.yml"
fi

if [[ $1 = "start" ]]; then
	command="$command up"
elif [[ $1 = "stop" ]]; then
	command="$command down"
elif [[ $1 = "rebuild" ]]; then
	command="$command build"
fi

eval "$command"
