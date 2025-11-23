"""
Pydantic models for Warframe data validation and graph node representation.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class WeaponNode(BaseModel):
    """Represents a Weapon node in Neo4j."""
    uniqueName: str = Field(..., description="Unique identifier from Warframe API")
    name: str
    accuracy: Optional[float] = None
    blockingAngle: Optional[int] = None
    codexSecret: Optional[bool] = None
    comboDuration: Optional[int] = None
    criticalChance: Optional[float] = None
    criticalMultiplier: Optional[float] = None
    damagePerShot: Optional[List[float]] = None
    description: Optional[str] = None
    excludeFromCodex: Optional[bool] = None
    fireRate: Optional[float] = None
    followThrough: Optional[float] = None
    heavyAttackDamage: Optional[int] = None
    heavySlamAttack: Optional[int] = None
    heavySlamRadialDamage: Optional[int] = None
    heavySlamRadius: Optional[int] = None
    magazineSize: Optional[int] = None
    masteryReq: Optional[int] = None
    maxLevelCap: Optional[int] = None
    multishot: Optional[int] = None
    noise: Optional[str] = None
    omegaAttenuation: Optional[float] = None
    primeOmegaAttenuation: Optional[float] = None
    procChance: Optional[float] = None
    productCategory: Optional[str] = None
    range: Optional[float] = None
    reloadTime: Optional[float] = None
    sentinel: Optional[bool] = None
    slamAttack: Optional[int] = None
    slamRadialDamage: Optional[int] = None
    slamRadius: Optional[int] = None
    slideAttack: Optional[int] = None
    slot: Optional[int] = None
    totalDamage: Optional[float] = None
    trigger: Optional[str] = None
    windUp: Optional[float] = None
    
    class Config:
        extra = "allow"  # Allow additional fields from API


class ResourceNode(BaseModel):
    """Represents a Resource node in Neo4j."""
    uniqueName: str = Field(..., description="Unique identifier from Warframe API")
    name: str
    codexSecret: Optional[bool] = None
    description: Optional[str] = None
    excludeFromCodex: Optional[bool] = None
    longDescription: Optional[str] = None
    parentName: Optional[str] = None
    primeSellingPrice: Optional[int] = None
    showInInventory: Optional[bool] = None
    
    class Config:
        extra = "allow"


class RecipeNode(BaseModel):
    """Represents a Recipe (Blueprint) node in Neo4j."""
    uniqueName: str = Field(..., description="Unique identifier from Warframe API")
    resultType: str = Field(..., description="What this recipe builds (uniqueName)")
    alwaysAvailable: Optional[bool] = None
    buildPrice: Optional[int] = None
    buildTime: Optional[int] = None
    codexSecret: Optional[bool] = None
    consumeOnUse: Optional[bool] = None
    excludeFromCodex: Optional[bool] = None
    ingredients: Optional[List[Dict[str, Any]]] = None
    num: Optional[int] = Field(None, description="Number of items produced")
    primeSellingPrice: Optional[int] = None
    secretIngredients: Optional[List[Dict[str, Any]]] = None
    skipBuildTimePrice: Optional[int] = None
    
    class Config:
        extra = "allow"


class RecipeIngredient(BaseModel):
    """Represents an ingredient in a recipe."""
    ItemType: str = Field(..., description="uniqueName of the required resource")
    ItemCount: int = Field(..., description="Quantity required")
    ProductCategory: Optional[str] = None


class CategoryNode(BaseModel):
    """Represents a Category node (e.g., Pistols, MeleeWeapons)."""
    name: str = Field(..., description="Category name from productCategory")


# Relationship models (for documentation and type hints)
class RequiresRelationship(BaseModel):
    """Recipe REQUIRES Resource relationship."""
    from_node: str = Field(..., description="Recipe uniqueName")
    to_node: str = Field(..., description="Resource uniqueName")
    quantity: int = Field(..., description="Amount required")


class BuildsRelationship(BaseModel):
    """Recipe BUILDS Item relationship."""
    from_node: str = Field(..., description="Recipe uniqueName")
    to_node: str = Field(..., description="Item uniqueName (resultType)")
    quantity: int = Field(1, description="Amount produced")


class BelongsToRelationship(BaseModel):
    """Item BELONGS_TO Category relationship."""
    from_node: str = Field(..., description="Item uniqueName")
    to_node: str = Field(..., description="Category name")
