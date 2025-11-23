"""
Ingest Warframe data into Neo4j graph database.
Loads Weapons, Resources, and Recipes with their relationships.
"""
from neo4j import GraphDatabase
import json
import os
import sys
from typing import List, Dict, Any
from pydantic import ValidationError

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE
from graph.models import WeaponNode, ResourceNode, RecipeNode

class Neo4jIngestion:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        self.data_dir = "data_raw"
        
    def close(self):
        self.driver.close()
    
    def clear_database(self):
        """Clear all nodes and relationships (use with caution!)"""
        with self.driver.session(database=NEO4J_DATABASE) as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("✓ Database cleared")
    
    # ==================== RESOURCE INGESTION ====================
    
    def ingest_resources(self):
        """Load all resources from ExportResources_en.json"""
        filepath = os.path.join(self.data_dir, "ExportResources_en.json")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        resources = data.get("ExportResources", [])
        print(f"\nIngesting {len(resources)} resources...")
        
        with self.driver.session(database=NEO4J_DATABASE) as session:
            for i, resource_data in enumerate(resources):
                try:
                    # Validate with Pydantic
                    resource = ResourceNode(**resource_data)
                    
                    # Create node in Neo4j with all fields
                    session.run("""
                        MERGE (r:Resource {uniqueName: $uniqueName})
                        SET r += $props
                    """, uniqueName=resource.uniqueName, props=resource.model_dump(exclude={'uniqueName'}, exclude_none=True))
                    
                    if (i + 1) % 500 == 0:
                        print(f"  Processed {i + 1}/{len(resources)} resources...")
                        
                except ValidationError as e:
                    print(f"  Warning: Validation error for resource: {resource_data.get('uniqueName', 'unknown')}")
                    print(f"    Error details: {e}")
                except Exception as e:
                    print(f"  Error ingesting resource: {e}")
        
        print(f"✓ Ingested {len(resources)} resources")
    
    # ==================== WEAPON INGESTION ====================
    
    def ingest_weapons(self):
        """Load all weapons from ExportWeapons_en.json"""
        filepath = os.path.join(self.data_dir, "ExportWeapons_en.json")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        weapons = data.get("ExportWeapons", [])
        print(f"\nIngesting {len(weapons)} weapons...")
        
        categories = set()
        
        with self.driver.session(database=NEO4J_DATABASE) as session:
            for i, weapon_data in enumerate(weapons):
                try:
                    # Validate with Pydantic
                    weapon = WeaponNode(**weapon_data)
                    
                    # Create weapon node with all fields
                    weapon_dict = weapon.model_dump(exclude_none=True)
                    # Convert damagePerShot list to string for storage (Neo4j doesn't handle lists well in SET +=)
                    if 'damagePerShot' in weapon_dict and weapon_dict['damagePerShot']:
                        weapon_dict['damagePerShot'] = str(weapon_dict['damagePerShot'])
                    
                    session.run("""
                        MERGE (w:Weapon {uniqueName: $uniqueName})
                        SET w += $props
                    """, uniqueName=weapon.uniqueName, props={k: v for k, v in weapon_dict.items() if k != 'uniqueName'})
                    
                    # Track category for creating category nodes
                    if weapon.productCategory:
                        categories.add(weapon.productCategory)
                    
                    if (i + 1) % 100 == 0:
                        print(f"  Processed {i + 1}/{len(weapons)} weapons...")
                        
                except ValidationError as e:
                    print(f"  Warning: Validation error for weapon: {weapon_data.get('name', 'unknown')}")
                except Exception as e:
                    print(f"  Error ingesting weapon: {e}")
        
        print(f"✓ Ingested {len(weapons)} weapons")
        
        # Create category nodes and relationships
        self._create_weapon_categories(categories)
    
    def _create_weapon_categories(self, categories: set):
        """Create category nodes and link weapons to them"""
        print(f"\nCreating {len(categories)} weapon categories...")
        
        with self.driver.session(database=NEO4J_DATABASE) as session:
            for category in categories:
                # Create category node
                session.run("""
                    MERGE (c:Category {name: $name})
                """, name=category)
                
                # Link weapons to category
                session.run("""
                    MATCH (w:Weapon {productCategory: $category})
                    MATCH (c:Category {name: $category})
                    MERGE (w)-[:BELONGS_TO]->(c)
                """, category=category)
        
        print(f"✓ Created {len(categories)} categories and linked weapons")
    
    # ==================== RECIPE INGESTION ====================
    
    def ingest_recipes(self):
        """Load all recipes from ExportRecipes_en.json"""
        filepath = os.path.join(self.data_dir, "ExportRecipes_en.json")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        recipes = data.get("ExportRecipes", [])
        print(f"\nIngesting {len(recipes)} recipes...")
        
        with self.driver.session(database=NEO4J_DATABASE) as session:
            for i, recipe_data in enumerate(recipes):
                try:
                    # Validate with Pydantic
                    recipe = RecipeNode(**recipe_data)
                    
                    # Create recipe node with all fields (except ingredients which are relationships)
                    session.run("""
                        MERGE (r:Recipe {uniqueName: $uniqueName})
                        SET r += $props
                    """, uniqueName=recipe.uniqueName, 
                        props=recipe.model_dump(exclude={'uniqueName', 'ingredients', 'secretIngredients'}, exclude_none=True))
                    
                    if (i + 1) % 500 == 0:
                        print(f"  Processed {i + 1}/{len(recipes)} recipes...")
                        
                except ValidationError as e:
                    print(f"  Warning: Validation error for recipe: {recipe_data.get('uniqueName', 'unknown')}")
                    print(f"    Error details: {e}")
                except Exception as e:
                    print(f"  Error ingesting recipe: {e}")
        
        print(f"✓ Ingested {len(recipes)} recipes")
        
        # Create relationships after all nodes exist
        self._create_recipe_relationships(recipes)
    
    def _create_recipe_relationships(self, recipes: List[Dict[str, Any]]):
        """Create REQUIRES and BUILDS relationships for recipes"""
        print(f"\nCreating recipe relationships...")
        
        requires_count = 0
        builds_count = 0
        
        with self.driver.session(database=NEO4J_DATABASE) as session:
            for recipe_data in recipes:
                recipe_unique = recipe_data.get('uniqueName')
                result_type = recipe_data.get('resultType')
                ingredients = recipe_data.get('ingredients', [])
                
                # Create BUILDS relationship (Recipe -> Weapon/Resource)
                if result_type:
                    # Try matching with Weapon first
                    result = session.run("""
                        MATCH (recipe:Recipe {uniqueName: $recipeUnique})
                        MATCH (item:Weapon {uniqueName: $resultType})
                        MERGE (recipe)-[:BUILDS {quantity: $quantity}]->(item)
                        RETURN count(*) as cnt
                    """, recipeUnique=recipe_unique, resultType=result_type, 
                         quantity=recipe_data.get('num', 1))
                    
                    if result.single()['cnt'] == 0:
                        # Try Resource if Weapon didn't match
                        result = session.run("""
                            MATCH (recipe:Recipe {uniqueName: $recipeUnique})
                            MATCH (item:Resource {uniqueName: $resultType})
                            MERGE (recipe)-[:BUILDS {quantity: $quantity}]->(item)
                            RETURN count(*) as cnt
                        """, recipeUnique=recipe_unique, resultType=result_type,
                             quantity=recipe_data.get('num', 1))
                        
                        if result.single()['cnt'] > 0:
                            builds_count += 1
                    else:
                        builds_count += 1
                
                # Create REQUIRES relationships (Recipe -> Resource/Component)
                for ingredient in ingredients:
                    item_type = ingredient.get('ItemType')
                    item_count = ingredient.get('ItemCount', 1)
                    
                    if item_type:
                        # Try matching with Resource
                        result = session.run("""
                            MATCH (recipe:Recipe {uniqueName: $recipeUnique})
                            MATCH (resource:Resource {uniqueName: $itemType})
                            MERGE (recipe)-[:REQUIRES {quantity: $quantity}]->(resource)
                            RETURN count(*) as cnt
                        """, recipeUnique=recipe_unique, itemType=item_type, quantity=item_count)
                        
                        if result.single()['cnt'] > 0:
                            requires_count += 1
        
        print(f"✓ Created {builds_count} BUILDS relationships")
        print(f"✓ Created {requires_count} REQUIRES relationships")
    
    # ==================== MAIN INGESTION ====================
    
    def ingest_all(self, clear_first=False):
        """Ingest all data in the correct order"""
        print("=" * 60)
        print("Starting Warframe Data Ingestion")
        print("=" * 60)
        
        if clear_first:
            response = input("\n⚠️  Clear all existing data? (yes/no): ")
            if response.lower() == 'yes':
                self.clear_database()
            else:
                print("Skipping database clear...")
        
        # Ingest in order: Resources -> Weapons -> Recipes (so relationships work)
        self.ingest_resources()
        self.ingest_weapons()
        self.ingest_recipes()
        
        print("\n" + "=" * 60)
        print("✓ Ingestion Complete!")
        print("=" * 60)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print database statistics"""
        with self.driver.session(database=NEO4J_DATABASE) as session:
            # Count nodes
            result = session.run("MATCH (n) RETURN labels(n)[0] as label, count(*) as count")
            print("\nNode Counts:")
            for record in result:
                print(f"  {record['label']}: {record['count']}")
            
            # Count relationships
            result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(*) as count")
            print("\nRelationship Counts:")
            for record in result:
                print(f"  {record['type']}: {record['count']}")

def main():
    ingestion = Neo4jIngestion()
    
    try:
        # Run full ingestion (clear_first=True to start fresh)
        ingestion.ingest_all(clear_first=True)
    finally:
        ingestion.close()

if __name__ == "__main__":
    main()
