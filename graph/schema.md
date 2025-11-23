# Warframe Graph Schema

## Overview
This document defines the Neo4j graph schema for the Warframe knowledge graph, including nodes, relationships, and their properties.

## Node Types

### 1. `:Weapon`
Represents weapons from ExportWeapons_en.json

**Properties:**
- `uniqueName` (STRING, UNIQUE, PRIMARY KEY) - Warframe API unique identifier
- `name` (STRING) - Display name
- `description` (STRING) - Weapon description
- `productCategory` (STRING) - Category (e.g., "Pistols", "Rifles", "Melee")
- `totalDamage` (FLOAT) - Total damage per shot
- `criticalChance` (FLOAT) - Critical hit chance (0-1)
- `criticalMultiplier` (FLOAT) - Critical damage multiplier
- `procChance` (FLOAT) - Status effect chance (0-1)
- `fireRate` (FLOAT) - Rounds per second
- `masteryReq` (INTEGER) - Mastery rank requirement
- `magazineSize` (INTEGER) - Ammo capacity
- `reloadTime` (FLOAT) - Reload time in seconds
- `accuracy` (FLOAT) - Weapon accuracy
- `codexSecret` (BOOLEAN) - Whether hidden in codex

**Example:**
```cypher
CREATE (w:Weapon {
  uniqueName: "/Lotus/Weapons/Tenno/Pistols/PrimeLex/PrimeLex",
  name: "Lex Prime",
  description: "The Lex Prime is a powerful, accurate pistol...",
  productCategory: "Pistols",
  totalDamage: 180.0,
  criticalChance: 0.25,
  criticalMultiplier: 2.0,
  masteryReq: 8
})
```

### 2. `:Resource`
Represents resources, materials, and items from ExportResources_en.json

**Properties:**
- `uniqueName` (STRING, UNIQUE, PRIMARY KEY)
- `name` (STRING) - Display name
- `description` (STRING) - Resource description
- `parentName` (STRING) - Parent type/category
- `codexSecret` (BOOLEAN)
- `excludeFromCodex` (BOOLEAN)
- `showInInventory` (BOOLEAN)

**Example:**
```cypher
CREATE (r:Resource {
  uniqueName: "/Lotus/Types/Game/CatbrowPet/CatbrowGeneticSignature",
  name: "Kavat Genetic Code",
  description: "Contains the genetic code sequence of a Kavat.",
  parentName: "/Lotus/Types/Items/MiscItems/ResourceItem"
})
```

### 3. `:Recipe`
Represents blueprints and recipes from ExportRecipes_en.json

**Properties:**
- `uniqueName` (STRING, UNIQUE, PRIMARY KEY)
- `resultType` (STRING) - uniqueName of what this recipe builds
- `buildPrice` (INTEGER) - Credits cost
- `buildTime` (INTEGER) - Build time in seconds
- `skipBuildTimePrice` (INTEGER) - Platinum cost to rush
- `consumeOnUse` (BOOLEAN) - Whether recipe is consumed
- `num` (INTEGER) - Quantity produced
- `codexSecret` (BOOLEAN)

**Example:**
```cypher
CREATE (bp:Recipe {
  uniqueName: "/Lotus/Weapons/Tenno/Pistols/PrimeLex/PrimeLexBlueprint",
  resultType: "/Lotus/Weapons/Tenno/Pistols/PrimeLex/PrimeLex",
  buildPrice: 15000,
  buildTime: 43200,
  num: 1
})
```

### 4. `:Category`
Represents item categories (derived from productCategory field)

**Properties:**
- `name` (STRING, UNIQUE, PRIMARY KEY) - Category name

**Examples:** "Pistols", "Rifles", "Melee", "Sentinels", "Warframes"

---

## Relationships

### 1. `(:Recipe)-[:REQUIRES]->(:Resource)`
A recipe requires a specific resource/ingredient

**Properties:**
- `quantity` (INTEGER) - Amount required

**Example:**
```cypher
MATCH (recipe:Recipe {uniqueName: "/Lotus/Weapons/Tenno/Pistols/PrimeLex/PrimeLexBlueprint"})
MATCH (resource:Resource {uniqueName: "/Lotus/Types/Items/MiscItems/OrokinCell"})
CREATE (recipe)-[:REQUIRES {quantity: 5}]->(resource)
```

### 2. `(:Recipe)-[:BUILDS]->(:Weapon|:Resource)`
A recipe builds/produces a specific item

**Properties:**
- `quantity` (INTEGER) - Amount produced (from recipe.num)

**Example:**
```cypher
MATCH (recipe:Recipe {uniqueName: "/Lotus/Weapons/Tenno/Pistols/PrimeLex/PrimeLexBlueprint"})
MATCH (weapon:Weapon {uniqueName: "/Lotus/Weapons/Tenno/Pistols/PrimeLex/PrimeLex"})
CREATE (recipe)-[:BUILDS {quantity: 1}]->(weapon)
```

### 3. `(:Weapon)-[:BELONGS_TO]->(:Category)`
An item belongs to a category

**No properties**

**Example:**
```cypher
MATCH (weapon:Weapon {name: "Lex Prime"})
MATCH (category:Category {name: "Pistols"})
CREATE (weapon)-[:BELONGS_TO]->(category)
```

---

## Indexes and Constraints

```cypher
-- Unique constraints (also create indexes)
CREATE CONSTRAINT weapon_unique IF NOT EXISTS
FOR (w:Weapon) REQUIRE w.uniqueName IS UNIQUE;

CREATE CONSTRAINT resource_unique IF NOT EXISTS
FOR (r:Resource) REQUIRE r.uniqueName IS UNIQUE;

CREATE CONSTRAINT recipe_unique IF NOT EXISTS
FOR (bp:Recipe) REQUIRE bp.uniqueName IS UNIQUE;

CREATE CONSTRAINT category_unique IF NOT EXISTS
FOR (c:Category) REQUIRE c.name IS UNIQUE;

-- Additional indexes for common queries
CREATE INDEX weapon_name IF NOT EXISTS FOR (w:Weapon) ON (w.name);
CREATE INDEX resource_name IF NOT EXISTS FOR (r:Resource) ON (r.name);
CREATE INDEX weapon_category IF NOT EXISTS FOR (w:Weapon) ON (w.productCategory);
```

---

## Sample Queries

### Find all resources needed for a weapon
```cypher
MATCH (w:Weapon {name: "Lex Prime"})
MATCH (recipe:Recipe)-[:BUILDS]->(w)
MATCH (recipe)-[r:REQUIRES]->(resource:Resource)
RETURN resource.name AS resource, r.quantity AS quantity
```

### Find all weapons in a category
```cypher
MATCH (w:Weapon)-[:BELONGS_TO]->(c:Category {name: "Pistols"})
RETURN w.name, w.totalDamage, w.masteryReq
ORDER BY w.totalDamage DESC
```

### Find recipes that require a specific resource
```cypher
MATCH (resource:Resource {name: "Orokin Cell"})
MATCH (recipe:Recipe)-[r:REQUIRES]->(resource)
MATCH (recipe)-[:BUILDS]->(item)
RETURN item.name AS builds, r.quantity AS needed
```

---

## Future Extensions

### Additional Nodes (Phase 2+)
- `:Warframe` - From ExportWarframes_en.json
- `:Ability` - From ExportAbilities in ExportWarframes_en.json
- `:Mod` - From ExportUpgrades_en.json
- `:Sentinel` - From ExportSentinels_en.json

### Additional Relationships
- `(:Warframe)-[:HAS_ABILITY]->(:Ability)`
- `(:Warframe)-[:USES]->(:Weapon)` - Based on slot compatibility
- `(:Mod)-[:COMPATIBLE_WITH]->(:Weapon|:Warframe)`
- `(:Resource)-[:OBTAINED_FROM]->(:Location)` - If location data added
