import ldap
from pathlib import Path
from configparser import ConfigParser
import threading

import n4d.server.core
import n4d.responses

import time

class CDC:

    GROUP_NOT_EXISTS = -10

    def __init__(self):
        self.load_configuration()
        self.list_of_queries = {}
        self.core = n4d.server.core.Core.get_core()
        self.semaphore = True
        self.cache_users = {"students":[10004, []], "teachers":[10003,[]] }
        self.users_timeout = {}
    #def __init__

    @property
    def identifier(self):
        '''
            This identifier go back to 0 when list_of_queries is void. So identifier not increase to big numbers 
        '''
        result = 0
        if len(self.list_of_queries.keys()) > 0: 
            result = list(self.list_of_queries.keys())[-1]
        return result

    def load_configuration( self ):
        self.config_path = Path( "/etc/sssd/sssd.conf" )
        self.sssd_config = ConfigParser()
        if self.config_path.exists():
            self.sssd_config.read( str( self.config_path ) )
            self.ldap_config = self.sssd_config[ "domain/EDU.GVA.ES" ]
            self.base_dn = self.ldap_config["ldap_search_base"]

    #def load_configuration

    def load_connection(self):
        if self.semaphore:
            self.semaphore = False
            self.ldap = ldap.initialize( self.ldap_config[ "ldap_uri" ] )
            self.ldap.set_option( ldap.VERSION, ldap.VERSION3 )
            self.ldap.bind_s( self.ldap_config[ "ldap_default_bind_dn" ], self.ldap_config[ "ldap_default_authtok" ] )
            self.semaphore = True


    def push_query( self, user ):
        '''
            Async function
            Add query in pool and return identifier for polling later
        '''
        #return query_id
        #async
        identifier = self.identifier + 1
        self.list_of_queries[identifier] = threading.Thread(target=self._push_query, args=(user, identifier))
        self.list_of_queries[identifier].start()
        return n4d.responses.build_successful_call_response(identifier)
    #def push_query


    def _push_query(self, user, identifier):
        self.load_connection()
        
        if user in self.users_timeout and self.users_timeout[user] <= (time.time() - 60 ):
            del(self.list_of_queries[identifier])
            return

        self.users_timeout[user] = time.time()
        list_groups = []
        dn_user_list = [ x[0] for x in self.ldap.search_s(self.base_dn, ldap.SCOPE_SUBTREE, "(cn={name})".format(name=user),["dn"]) if x[0] is not None ]
        for dn_user in dn_user_list:
            list_groups = list_groups  + [ x[1]['cn'][0].decode('utf-8') for x in self.ldap.search_s(self.base_dn, ldap.SCOPE_SUBTREE, "(member={name})".format(name=dn_user),["cn"]) if x[0] is not None ]
        
        for x in list(set(list_groups)):
            if x.lower().startswith("alu"):
                self.cache_users["students"][1].append(user)
                self.cache_users["students"][1] = list(set(self.cache_users["students"][1]))
            if x.lower().startswith("doc"):
                self.cache_users["teachers"][1].append(user)
                self.cache_users["teachers"][1] = list(set(self.cache_users["teachers"][1]))

        # Remove query from list becauseof this finish
        del(self.list_of_queries[identifier])
    #def _push_query 

    def wait_for_queries(self):
        '''
            Sync function
            wait to all queries finish
        '''

        list_of_queries = list(self.list_of_queries.keys())
        for x in list_of_queries:
            if x in self.list_of_queries:
                self.list_of_queries[x].join()
        return n4d.responses.build_successful_call_response(True)
    #def wait_for_queries

    def query_status(self, identifier):
        '''
            get status query
        '''
        return self.list_of_queries[identifier].is_alive()
    #def query_status

    def getgrall(self):
        '''
            Return all groups
        '''
        return n4d.responses.build_successful_call_response( self.cache_users )
    #def getgrall

    def getgrgid(self, gid):
        '''
            If exists group with gid return its name
        '''
        for x in self.cache_users.keys():
            if self.cache_users[x][0] == gid:
                return n4d.responses.build_successful_call_response(x)
        return n4d.responses.build_failed_call_response(CDC.GROUP_NOT_EXISTS)
    #def getgrgid

    def getgrnam(self, name):
        '''
            If exists group with name return its gid
        '''
        if name in self.cache_users.keys():
            return n4d.responses.build_successful_call_response(self.cache_users[name][0])
        return n4d.responses.build_failed_call_response(CDC.GROUP_NOT_EXISTS)
    #def getgrnam

    def clear_cache(self):
        for x in self.cache_users.keys():
            self.cache_users[x][1] = []
        return n4d.responses.build_successful_call_response( True )
    #def clear_cache
