#!/bin/bash

# prints colored text
print_style () {

    if [ "$2" == "info" ] ; then
        COLOR="4;34m";
    elif [ "$2" == "success" ] ; then
        COLOR="1;92m";
    elif [ "$2" == "warning" ] ; then
        COLOR="4;93m";
    elif [ "$2" == "danger" ] ; then
        COLOR="1;91m";
    else #default color
        COLOR="0m";
    fi

    STARTCOLOR="\e[$COLOR";
    ENDCOLOR="\e[0m";

    printf "$STARTCOLOR%b$ENDCOLOR\n" "$1";
}

print_style "Checking if everything is correct" "info"
python3 manage.py check --deploy

print_style "\nCollecting static files" "info"
python3 manage.py collectstatic --no-input

print_style "\nDumping database in case of migrations failure" "danger"
_today_=$(date +'%d-%m-%Y')
# sudo touch ~/database_backup/db-"$_today_".json

python3 manage.py dumpdata --exclude auth.permission --exclude contenttypes > ./database_backup/db-"$_today_".json
# python3 manage.py dumpdata --exclude auth.permission --exclude contenttypes --exclude admin.logentry --exclude sessions.session > ./database_backup/db-"$_today_".json

print_style "\nCreate migrations for the different applications" "info"
python3 manage.py makemigrations homepage
python3 manage.py makemigrations client
python3 manage.py makemigrations static_pages_and_forms
python3 manage.py makemigrations portfolio

print_style "\nApplying the migrations" "warning"
python3 manage.py migrate

print_style "\nRestart the system" "warning"
sudo systemctl daemon-reload
sudo systemctl restart gunicorn.service
sudo systemctl restart nginx.service
sudo systemctl restart uwsgi.service

print_style "\nDONE" "success"
