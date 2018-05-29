#!/bin/bash

BACKIT_DIR=$(dirname "${BASH_SOURCE[0]}")
BACKIT_DIR=$(readlink -f $BACKIT_DIR)
ALIAS_DIR=/usr/local/bin

read -p "Install aliases to $ALIAS_DIR? [Y/n]: " -n1 yn
echo ''

if [[ "$yn" =~ ^[Yy]$ ]]; then
	sudo ln -s $BACKIT_DIR/bin/backit-up $ALIAS_DIR/backit-up
	sudo ln -s $BACKIT_DIR/bin/backit-out $ALIAS_DIR/backit-out
	sudo ln -s $BACKIT_DIR/bin/backit-clean $ALIAS_DIR/backit-clean

	echo "Aliases installed."
else
	read -p "Add $BACKIT_DIR to your PATH instead? [Y/n]: " -n1 yn
	echo ''

	if [[ "$yn" =~ ^[Yy]$ ]]; then
		PATH=$PATH:$BACKIT_DIR/bin
		echo "export PATH=\$PATH:$BACKIT_DIR/bin" >> ~/.bash_profile

		echo "PATH updated."
	fi
fi
