"""
Test Neo4j connection
"""
from neo4j import GraphDatabase
import sys
import os

# Add parent directory to path to import config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

def test_connection():
    """Test connection to Neo4j database."""
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        
        # Connect to the specific database
        with driver.session(database="warframebotdata") as session:
            result = session.run("RETURN 'Connection successful!' AS message")
            record = result.single()
            print(f"✓ {record['message']}")
            print(f"✓ Connected to database: warframebotdata")
            
            # Check database info
            result = session.run("CALL dbms.components() YIELD name, versions, edition")
            for record in result:
                print(f"✓ Neo4j {record['name']}: {record['versions'][0]} ({record['edition']})")
        
        driver.close()
        print("\n✓ All tests passed! Ready to ingest data.")
        return True
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Neo4j database is started in Neo4j Desktop")
        print("2. Verify password in config.py matches Neo4j Desktop")
        print("3. Check that bolt port 7687 is accessible")
        return False

if __name__ == "__main__":
    test_connection()
