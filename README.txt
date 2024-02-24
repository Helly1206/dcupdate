dcupdate - v0.8.0

dcupdate - Docker Compose update(r)
======== = ====== ======= =========

dcupdate is a simple service that updates docker compose containers on request. This tool is designed to manually
update home assistant from a docker home assistant core installation. Auotmatic updating watch watchtower may 
be preferred but if a new version breaks some automations, it might end up non functioning. I do update home 
assistant manually at a moment that fits me now and check if everything is working after the update.

I use the version integration to check for a new version. Because docker cannot be called from a docker instance,
the service runs on the host system and via the doupdate command (added bash or python) as a shell command the 
instance can be updated.

Of course this script can be integrated and used for all docker (compose) containers and not only for home assistant.

dcupdate works with portainer, but also with standard docker compose containers

Known issues: when a stack is not running, it cannot be updated. Start the stack manually first if it is not running for 
whatever reason.

Installation:
-------------
Manual installation can be done as follows:
- Browse to: https://github.com/Helly1206/smarthome
- Click the 'Clone or Download' button
- Click 'Download Zip'
- Unzip the zip file to a temporary location
- Open a terminal at this location
- Enter: 'sudo ./install.sh'
- Wait and answer the questions:
	Do you want to install an automatic startup service for dcupdate (Y/n)?
   		Default = Y
   		If you want to automatically start dcupdate during startup (or don't know), answer Y to this question.
   		If you do not want to install an automatic startup script, answer N to this question.

Manually run dcupdate:
-------- --- ---------
When you didn't install an automatic startup service for dcupdate
- Run by /opt/dcupdate/dcupdate.py

No command line options available, except for displaying help

Installer options:
--------- --------
sudo ./install.sh    --> Installs dcupdate
sudo ./install.sh -u --> Uninstalls dcupdate
sudo ./install.sh -c --> Deletes compiled files in install folder (only required when copying or zipping the install folder)
sudo ./install.sh -d --> Builds debian packages

Package install:
------- --------
dcupdate installs automatically from deb package/ apt repository (only for debian based distros like debian or ubuntu).
Just enter: 'sudo apt install dcupdate' after adding the repository
see: https://github.com/Helly1206/hellyrepo for installing the repository

Configuration:
--------------
In /etc/dcupdate.yml, the configuration file is found.
Example:
#dcupdate settings file
#  logging: info, debug, error
#  volumes: linked volumes as list (e.g. for portainer /opt/portainer:/data)
dcupdate:
  logging: info
  volumes:
    - /opt/portainer:/data

Usage:
------
With the service running, just enter /opt/dcupdate/doupdate.py <<stack or container name>>
or /opt/dcupdate/doupdate.sh <<stack or container name>>
Of course the code to send data through the socket can also be copied to your own application
multple stacks can be updated separated by commas and enter - to update the root stack

That's all for now ...

Have fun

Please send Comments and Bugreports to hellyrulez@home.nl
