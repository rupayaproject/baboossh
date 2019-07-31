import os
import re
import configparser
import ipaddress
from src.params import dbConn,Extensions
from src.host import Host
from src.endpoint import Endpoint
from src.user import User
from src.creds import Creds
from src.connection import Connection



config = configparser.ConfigParser()
config.read('config.ini')
if "DEFAULT" not in config or "workspaces" not in config['DEFAULT']:
    print("Invalid config file")
    exit()


class Workspace():

#################################################################
###################           INIT            ###################
#################################################################

    @classmethod
    def create(cls,name):
        if name == "":
            print("Cannot use workspace with empty name")
            raise ValueError
        if re.match('^[\w_\.-]+$', name) is None:
            print('Invalid characters in workspace name. Allowed characters are letters, numbers and ._-')
            raise ValueError
        workspaceFolder = os.path.join(config['DEFAULT']['workspaces'],name)
        if not os.path.exists(workspaceFolder):
            try:
                os.mkdir(workspaceFolder)
            except OSError:
                print ("Creation of the directory %s failed" % workspaceFolder)
                raise OSError
            print("Workspace "+name+" created")
        else:
            print("Workspace already exists")
            raise ValueError
        #create database
        dbConn.build(name)
        return Workspace(name)

    def __init__(self,name):
        if name == "":
            raise ValueError("Cannot use workspace with empty name")
        if re.match('^[\w_\.-]+$', name) is None:
            print('Invalid characters in workspace name. Allowed characters are letters, numbers and ._-')
            raise ValueError
        workspaceFolder = os.path.join(config['DEFAULT']['workspaces'],name)
        if not os.path.exists(workspaceFolder):
            raise ValueError("Workspace "+name+" does not exist")
        dbConn.connect(name)
        self.name = name
        self.options = {
            "endpoint":None,
            "user":None,
            "creds":None,
            "payload":None,
                }

#################################################################
###################         ENDPOINTS         ###################
#################################################################

    #Checks if param is a valid IP (v4 or v6)
    def checkIsIP(self,ip):
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            return False
        return True

    #Manually add a endpoint
    def addEndpoint_Manual(self,ip,port):
        if not self.checkIsIP(ip):
            print("The address given isn't a valid IP")
            raise ValueError
        if not port.isdigit():
            print("The port given isn't a positive integer")
            raise ValueError

        newEndpoint = Endpoint(ip,port)
        newEndpoint.save()

#################################################################
###################           USERS           ###################
#################################################################

    #Manually add a user
    def addUser_Manual(self,name):
        newUser = User(name)
        newUser.save()

#################################################################
###################           CREDS           ###################
#################################################################

    def addCreds_Manual(self,credsType):
        credsContent = Extensions.getAuthMethod(credsType).build()
        newCreds = Creds(credsType,credsContent)
        newCreds.save()

#################################################################
###################          OPTIONS          ###################
#################################################################

    def setOption(self,option,value):
        if option == 'target' and '@' in value and ':' in value:
            connection = Connection.fromTarget(value)
            if connection == None:
                return
            self.options['endpoint'] = connection.getEndpoint()
            self.options['user'] = connection.getUser()
            self.options['creds'] = connection.getCred()
            for option in ['endpoint','user','creds']:
                print(option+" => "+str(self.getOption(option)))
            return 

        if not option in self.options.keys():
            raise ValueError(option+" isn't a valid option.")
        if value != "":
            value = value.strip()
            if option == "endpoint":
                endpoint = Endpoint.findByIpPort(value)
                if endpoint is None:
                    raise ValueError
                value = endpoint
            elif option == "user":
                user = User.findByUsername(value)
                if user is None:
                    raise ValueError
                value = user
            elif option == "creds":
                if value[0] == '#':
                    credId = value[1:]
                else:
                    credId = value
                creds = Creds.find(credId)
                if creds is None:
                    raise ValueError
                value = creds
            elif option == "payload":
                value = Extensions.getPayload(value)
        else:
            self.options[option] = None
    
        self.options[option] = value
        print(option+" => "+str(self.getOption(option)))

#################################################################
###################        CONNECTIONS        ###################
#################################################################

    def connect(self,endpoint,user,cred):
        connection = Connection(endpoint,user,cred)
        connection.connect()

    def run(self,endpoint,user,cred,payload):
        connection = Connection(endpoint,user,cred)
        connection.run(payload)

    def connectTarget(self,arg):
        connection = Connection.fromTarget(arg)
        connection.connect()

    def runTarget(self,arg,payloadName):
        connection = Connection.fromTarget(arg)
        payload = Extensions.getPayload(payloadName)
        connection.run(payload)


#################################################################
###################          GETTERS          ###################
#################################################################

    def getName(self):
        return self.name

    def getHosts(self):
        return Host.findAll()

    def getEndpoints(self):
        endpoints = []
        for endpoint in Endpoint.findAll():
            endpoints.append(endpoint)
        return endpoints

    def getEndpointsList(self):
        endpoints = []
        for endpoint in Endpoint.findAll():
            endpoints.append(endpoint.ip+":"+endpoint.port)
        return endpoints
    
    def getTargetsValidList(self):
        connections = []
        for connection in Connection.findByWorking(True):
            connections.append(str(connection))
        return connections

    def getUsersList(self):
        users = []
        for user in User.findAll():
            users.append(str(user))
        return users

    def getUsers(self):
        return User.findAll()

    def getCreds(self):
        return Creds.findAll()

    def getCredsIdList(self):
        idList = []
        for cred in Creds.findAll():
            idList.append(str(cred.getId()))
        return idList

    def getOptions(self):
        return self.options.keys()

    def getOptionsValues(self):
        return self.options.items()

    def getOption(self,key):
        if key not in self.options.keys():
            raise ValueError()
        if self.options[key] == None:
            return None
        return self.options[key]

    def close(self):
        dbConn.close()
        print("Closing workspace "+self.name)


