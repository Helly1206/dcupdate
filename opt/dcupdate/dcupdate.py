#!/usr/bin/python3

# -*- coding: utf-8 -*-
#########################################################
# SCRIPT : dcupdate.py                                  #
#          update docker-compose stack from commandline #
#                                                       #
#          I. Helwegen 2024                             #
#########################################################

####################### IMPORTS #########################
import sys, os
from threading import Thread, Event
from time import sleep
from select import select
import subprocess
import signal
import socket
import queue
import logging
import logging.handlers
import locale
import json
try:
    import yaml
except ImportError:
    try:
        import pip
        try:
            package="pyyaml"
            if hasattr(pip, 'main'):
                pip.main(['install', package])
            else:
                pip._internal.main(['install', package])
        except:
            print("Unable to install required packages")
            print("yaml not installed")
            exit(1)
        import yaml
    except:
        print("Pip not installed, please install pip to continue")
        print("Unable to install the required packages")
        exit(1)

#########################################################

####################### GLOBALS #########################

APP_NAME = "dcupdate"
VERSION = "0.8.0"
HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65432  # Port to listen on (non-privileged ports are > 1023)
MAXCLIENTS = 5
YML_FILE = "/etc/dcupdate.yml"
ROOT = "<root>"

#########################################################

###################### FUNCTIONS ########################

#########################################################
# Class : updater                                       #
#########################################################
class updater(Thread):
    def __init__(self, basename = "", settings = {}):
        self.logger = logging.getLogger('{}.updater'.format(basename))
        self.settings = settings
        Thread.__init__(self)
        self.term = Event()
        self.term.clear()
        self.cmdqueue = queue.Queue()

    def __del__(self):
        del self.cmdqueue
        del self.term
        self.logger.info("finished")

    def terminate(self):
        self.term.set()

    def queueCmd(self, cmds):
        for cmd in cmds:
            self.cmdqueue.put(cmd.strip())

    def run(self):
        self.logger.info("running")
        while not self.term.is_set():
            try:
                stack = self.cmdqueue.get_nowait()
            except queue.Empty:
                sleep(1)
            else:
                if stack == "-" or stack == "":
                    stack = ROOT
                self.logger.info("Updating: {}".format(stack))
                location = self.getYamlLocation(stack)
                ok = False
                if location and not self.term.is_set():
                    ok = self.pull(stack, location)
                if ok and not self.term.is_set():
                    ok = self.down(stack)
                if ok and not self.term.is_set():
                    ok = self.up(stack, location)
                if ok and not self.term.is_set():
                    ok = self.cleanup()

    def checkDockerAvailable(self):
        avail = False
        # Only check for compose version >=2, if compose installed then docker should also be installed
        try:
            outp = self.dockerCommand("compose version -f json")
            joutp = json.loads(outp)
            if "version" in joutp:
                ver = joutp["version"]
                mver = 0
                try:
                    mver = int(ver[ver.index("v")+1:ver.index(".")])
                except:
                    pass
                if mver >= 2:
                    avail = True
                else:
                    self.logger.error("docker compose version v2.xx.x or higher required")
            else:
                self.logger.error("docker compose incorrect version information")    
        except Exception as e:
            try:
                outp = self.dockerCommand("version -f json")
            except Exception as e:
                self.logger.error("docker not installed")
            self.logger.error("docker compose not installed")
        return avail
    
    def getYamlLocation(self, stack):
        location = None
        self.logger.info("getting location for {}".format(stack))
        if stack == ROOT:
            location = ROOT
        else:
            try:
                outp = self.dockerCommand("compose ls --format json -a")
                containers = json.loads(outp)
                for container in containers:
                    if "Name" in container and "ConfigFiles" in container:
                        if container["Name"] == stack:
                            location = self.getAbsLocation(container["ConfigFiles"])
                            break
            except Exception as e:
                self.logger.error(e)
        self.logger.info("location for {}: {}".format(stack, location))
        return location
    
    def pull(self, stack, location):
        ok = False
        self.logger.info("pulling {}".format(stack))
        try:
            if stack == ROOT:
                outp = self.dockerCommand("compose pull --quiet")
            else:
                outp = self.dockerCommand("compose -f {} -p {} pull --quiet".format(location, stack))
            ok = True
            self.logger.info("pulled {}".format(stack))
        except Exception as e:
            self.logger.error(e)
        return ok
    
    def down(self, stack):
        ok = False
        self.logger.info("stopping {}".format(stack))
        try:
            if stack == ROOT:
                outp = self.dockerCommand("compose down")
            else:
                outp = self.dockerCommand("compose -p {} down".format(stack))
            ok = True
            self.logger.info("stopped {}".format(stack))
        except Exception as e:
            self.logger.error(e)
        return ok
    
    def up(self, stack, location):
        ok = False
        self.logger.info("starting {}".format(stack))
        try:
            if stack == ROOT:
                outp = self.dockerCommand("compose up -d")
            else:
                outp = self.dockerCommand("compose -f {} -p {} up -d".format(location, stack))
            ok = True
            self.logger.info("started {}".format(stack))
        except Exception as e:
            self.logger.error(e)
        return ok
    
    def cleanup(self):
        ok = False
        self.logger.info("cleaning up")
        try:
            outp = self.dockerCommand("image prune -af")
            self.logger.info(outp)
            ok = True
            self.logger.info("cleaned up")
        except Exception as e:
            self.logger.error(e)
        return ok
                
    def dockerCommand(self, cmd, timeout = 0):
        stdout = ""
        try:
            if timeout == 0:
                timeout = None
            out = subprocess.run("docker {}".format(cmd), shell=True, capture_output=True, input=None, timeout=timeout)
            stdout = out.stdout.decode("utf-8")
            if 0 != out.returncode:
                exc = ("Docker command failed.\n"
                "Command returned: {}\n"
                "Error message:\n{}").format(out.returncode, out.stdout.decode("utf-8"))
                raise Exception(exc)
        except subprocess.TimeoutExpired:
            exc = ("Docker command timed out.")
            raise Exception(exc)
        return stdout

    def getAbsLocation(self, location):
        if not os.path.isfile(location):
            origloc = location
            location = None
            if "volumes" in self.settings:
                for orig, replacement in self.settings["volumes"].items():
                    try:
                        if origloc.index(orig) == 0:
                            location = origloc.replace(orig, replacement)
                            if os.path.isfile(location):
                                break
                            else:
                                location = None
                    except:
                        pass
        return location          

#########################################################
# Class : dcupdate                                      #
#########################################################
class dcupdate(object):
    def __init__(self):
        self.settings = {}
        self.updater = None
        self.term = Event()
        self.term.clear()
        self.timeout = 1
        self.bufsize = 1024
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.setblocking(0)
        self.server_address = (HOST, PORT)
        self.maxclients = MAXCLIENTS
        self.inputs = [ self.server ]
        self.outputs = [ ]
        self.peers = {}
        self.logger = logging.getLogger(APP_NAME)
        self.logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler(sys.stdout)
        self.logger.addHandler(ch)
        locale.setlocale(locale.LC_TIME,'')
        strformat=("{} {}".format(locale.nl_langinfo(locale.D_FMT),locale.nl_langinfo(locale.T_FMT)))
        strformat=strformat.replace("%y", "%Y")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s', strformat)
        ch.setFormatter(formatter)
        self.logger.info("{} app, version {}".format(APP_NAME, VERSION))

    def __del__(self):
        self.server.close()
        del self.term

    def run(self, argv):
        signal.signal(signal.SIGINT, self.exit_app)
        signal.signal(signal.SIGTERM, self.exit_app)
        self.handleArgs(argv)
        self.setlogger()

        self.updater=updater(APP_NAME, self.settings)
        self.updater.start()
        if not self.updater.checkDockerAvailable():
            self.logger.error("Docker (compose) not installed on this system")
            self.logger.error("Please install Docker and Docker compose before able to use this app")
            self.exit_app(None, None)
            exit(1)

        self.server.bind(self.server_address)
        self.server.listen(self.maxclients)
        self.logger.debug('Listening up on {}, port {}'.format(self.server_address[0], self.server_address[1]))
        
        while not self.term.is_set():
            try:
                inputready, outputready, exceptready = select(self.inputs, self.outputs, self.inputs, self.timeout)
            except:
                continue

            if not (inputready or outputready or exceptready):
                continue
            for sock in inputready:
                if sock is self.server:
                    try:
                        connection, client_address = sock.accept()
                        connection.setblocking(0)
                    except:
                        continue
                    self.logger.debug('New connection from port {}'.format(str(client_address[1])))
                    self.inputs.append(connection)
                    self.peers[connection] = client_address
                else:
                    data = self.decode(self.receive(sock))
                    if data:
                        self.updater.queueCmd(data)
                    else:
                        self.logger.debug('Closing connection from {}'.format(str(self.peers[sock][1])))
                        self.inputs.remove(sock)
                        sock.close()
                        del self.peers[sock]

            for sock in outputready:
                pass

            for sock in exceptready:
                self.logger.error('Handling exceptional condition for {}'.format(str(self.peers[sock][1])))
                self.inputs.remove(sock)
                sock.close()
                del self.peers[sock]

    def receive(self, sock):
        packet = None
        try:
            packet = sock.recv(self.bufsize)
            if not packet:
                packet = None
        except:
            packet = None
        return packet
    
    def decode(self, data):
        if data:
            return data.decode("utf-8").strip().split(",")
        else:
            return None

    def handleArgs(self, argv):
        if len(sys.argv) > 1:
            arg = sys.argv[1]
            if arg == "-h" or arg == "--help":
                self.printHelp()
            else:
                self.logger.error("Incorrect argument entered")
                self.printError()
        try:
            with open(YML_FILE, "r") as f:
                try:
                    ysettings = yaml.safe_load(f)
                    if APP_NAME in ysettings:
                        for key, value in ysettings[APP_NAME].items():
                            if key == "volumes":
                                self.settings[key] = {}
                                for val in value:
                                    volume = val.split(":")
                                    if len(volume)>1:
                                        self.settings[key][volume[1].strip()]=volume[0].strip()
                            else:
                                self.settings[key] = value.strip()
                except:
                    self.logger.error("Error parsing yaml file")
                    self.printError()
        except:
            pass

    def setlogger(self):
        if "logging" in self.settings:
            if self.settings["logging"].lower() == "error":
                self.logger.setLevel(logging.ERROR)
            elif self.settings["logging"].lower() == "info":
                self.logger.setLevel(logging.INFO)         
    
    def printHelp(self):
        print("Option:")
        print("    -h, --help: print this help file and exit")
        print(" ")
        print("Enter options in /etc/dcupdate.yml")
        print("options: logging: info, debug, error")
        print("         volumes: linked volumes (e.g. for portainer /opt/portainer:/data)")
        exit(0)

    def printError(self):
        print("Enter {} -h for help".format(APP_NAME))
        exit(1)

    def exit_app(self, signum, frame):
        print("Exit app")
        self.term.set()
        if (self.updater != None):
            self.updater.terminate()
            self.updater.join(5)

#########################################################

######################### MAIN ##########################
if __name__ == "__main__":
    dcupdate().run(sys.argv)