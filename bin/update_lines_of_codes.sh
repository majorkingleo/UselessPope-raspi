#!/usr/bin/env bash

echo "<?php"
echo "\$lines_of_code = array();";

CC=$(find ~/UselessPope-Broker/src \
	~/UselessPope-Broker/common \
	~/UselessPope-Broker/db \
	~/UselessPope-Broker/config \
	-name "*.c*" -or -iname "*.h" | xargs wc -l | awk '/total/{ print $1; }')

PY=$(find ~/UselessPope-raspi/python -iname "*.py" | xargs wc -l | awk '/total/{ print $1; }')
PHP=$(find /var/www/papst/UselessPope-www/ -name "*.php" | xargs wc -l | awk '/total/{ print $1; }')
WEB=$(find /var/www/papst/UselessPope-www/lib /var/www/papst/UselessPope-www/js -name "*.css" -or -name "*.js" | xargs wc -l | awk '/total/{ print $1; }')
EMB=$(find ~/UselessPope-RemoteButton/RemoteButton/ -name "*.h" -or -name "*.ino" | xargs wc -l | awk '/total/{ print $1; }')

echo "\$lines_of_code[\"broker\"] = ${CC};"
echo "\$lines_of_code[\"python\"] = ${PY};"
echo "\$lines_of_code[\"php\"] = ${PHP};"
echo "\$lines_of_code[\"web\"] = ${WEB};"
echo "\$lines_of_code[\"arduino\"] = ${EMB};"

echo "?>";
