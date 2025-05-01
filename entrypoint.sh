#!/bin/bash

run(){
	echo $1
	eval $1
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
		*)    # unknown option
      echo "Error: Unknown option: $1" >&2
      exit 1
      ;;
	esac
done



run "flask db upgrade"
if [[ $dev_mode = true ]]; then
  run "flask --app dvm run --host 0.0.0.0 --debug"
else
  run "gunicorn -b 0.0.0.0:5000 -k gevent -t 10000 'app:app'"
fi
