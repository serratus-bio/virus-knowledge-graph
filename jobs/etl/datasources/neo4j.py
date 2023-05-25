import os

from neo4j import GraphDatabase


class Neo4jConnection:
    def __init__(self, uri, user, pwd):
        self._uri = uri
        self._user = user
        self._pwd = pwd
        self._driver = None
        try:
            self._driver = GraphDatabase.driver(
                self._uri, auth=(self._user, self._pwd))
        except Exception as e:
            print("Failed to create the driver:", e)

    def close(self):
        if self._driver is not None:
            self._driver.close()

    def query(self, query, parameters=None, db=None):
        assert self._driver is not None, "Driver not initialized!"
        session = None
        response = None
        try:
            session = self._driver.session(
                database=db) if db is not None else self._driver.session()
            response = list(session.run(query, parameters))
        except Exception as e:
            print("Query failed:", e)
        finally:
            if session is not None:
                session.close()
        return response


def get_connection():
    return Neo4jConnection(
        uri=os.environ.get('NEO4J_URI'),
        user=os.environ.get('NEO4J_USER'),
        pwd=os.environ.get('NEO4J_PASSWORD')
    )
