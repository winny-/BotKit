#!/bin/env bash

echo "This script needs admin privileges"
sudo echo "Thanks :3"

echo "Installing requirements"
sudo pip install -r requirements.txt -q

echo "Installing BotKit"
sudo python setup.py install

echo "All done!"