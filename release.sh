#!/usr/bin/env bash

# takes the tag as an argument (e.g. v0.1.0)
if [ -n "$1" ]; then
    if [[ "$1" =~ ^[0-9]{0,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        read -r -p "Are you sure to upgrade to v$1 ? [y/N] " response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]
        then
            # update the version in pyproject
            sed -i '' -E "s|version = \"[0-9].*\"|version = \"${1#v}\"|" pyproject.toml
            git add pyproject.toml
            sed -i '' -E "s|__version__ = \"[0-9].*\"|__version__ = \"${1#v}\"|" ggmail/__init__.py
            git add ggmail/__init__.py
            git commit -m "chore(release): prepare for v$1"
            git tag "v$1"
            git push --atomic origin main "v$1"
        else
            echo "Operation canceled"
        fi
    else
        echo "The version should be X.X.X"
    fi
else
	echo "Please provide a tag"
fi