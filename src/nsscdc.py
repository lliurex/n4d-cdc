import ldap
from pathlib import Path
from configparser import ConfigParser
import threading
import collections

import n4d.server.core
import n4d.responses

class NssCDC:
    def __ini__(self):
        self.load_configuration()
        self.list_of_queries = {}
        self.core = n4d.server.core.Core.get_core()
    #def __init__

    @property
    def identifier(self):
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
            self.ldap = ldap.initialize( self.ldap_config[ "ldap_uri" ] )
            self.ldap.set_option( ldap.VERSION, ldap.VERSION3 )
            self.ldap.bind_s( self.ldap_config[ "ldap_default_bind_dn" ], self.ldap_config[ "ldap_default_authtok" ] )
            # ldap_uri
            # ldap_search_base
            # ldap_default_bind_dn
            # ldap_default_authtok

    #def load_configuration

    def push_query( self, user ):

        #return query_id
        #async
        identifier = self.identifier + 1
        self.list_of_queries[identifier] = threading.Thread(target=self._push_query, args=(user, identifier))
        self.list_of_queries[identifier].start()
        return n4d.responses.build_successful_call_response(identifier)
    #def push_query


    def _push_query(self, user, identifier):

        
        # la que hace todas las busquedas en ldap AD

        # Remove query from list becauseof this finish
        del(self.list_of_queries[identifier])
    #def _push_query 

    def wait_for_queries(self):
        # espera a todas las consultas del active directory y rellenado de tablas
        # funciona como el sync
        pass
    #def wait_for_queries

    def query_status(self, identifier):
        # return bool
        # async
        pass
    #def query_status

    def getgrall(self):
        #sync

        result =  {"name":"students", "gid":"10003", "members":""}
        pass
    #def getgrall

    def getgrgid(self, identifier):
        #sync
        pass
    #def getgrgid

    def getgrnam(self, name):
        #sync
        pass
    #def getgrnam

    def clear_cache(self):
        pass
    #def clear_cache
