import json
import os
import numpy as np

weapon_file = 'data_raw/ExportRecipes_en.json'
if os.path.exists(weapon_file):
    with open(weapon_file, 'r') as f:
        weapon_data = json.load(f)
    
    # Find a specific item
    # product_categories = [k for x in weapon_data.get("ExportRecipes", []) for k in list(x.keys())]
    product_categories = [z for x in weapon_data.get("ExportRecipes", []) for k in x['ingredients'] for z in list(k.keys())]

    print(np.unique(product_categories))