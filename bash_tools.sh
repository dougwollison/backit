BACKIT_DIR=$(dirname "${BASH_SOURCE[0]}")

backit()
{
	local cmd=$1
	shift 1

	[ -z $cmd ] && echo "No command specified" && return 0
	[[ ! "$cmd" =~ ^up|out|clean$ ]] && echo "Command not recognized: $cmd" && return 0

	command "backit-$cmd" $@
}

_backit()
{
	local cur opts conf dir

	COMPREPLY=()

	cur="${COMP_WORDS[COMP_CWORD]}"

	case $COMP_CWORD in
		1)
			# command, list options
			opts="up out clean"
			;;
		2)
			# projects, list options
			opts=$(ls $BACKIT_DIR/conf/*.conf | tr '\n' '\0' | xargs -0 -n 1 basename -s .conf)
			;;
		3)
			# extra, proceed based on command
			if [ "${COMP_WORDS[1]}" == 'out' ]; then
				# archive command, list available folders
				conf=/opt/backit/conf/${COMP_WORDS[2]}.conf

				if [ -r "$conf" ]; then
					# get target_base from the config file
					dir=$(grep target_base $conf | cut -d '=' -f 2 | tr -d ' ')

					if [ -d "$dir" ]; then
						# scan for archives
						opts=$(ls $dir | grep 20*)
					fi
				fi
			fi
			;;
	esac

	COMPREPLY=($(compgen -W "$opts" -- ${cur}))

	return 0
}

complete -F _backit backit
