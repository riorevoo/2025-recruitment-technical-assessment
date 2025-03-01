from dataclasses import dataclass
from typing import List, Dict, Union
from flask import Flask, request, jsonify
import re


# ==== Type Definitions, feel free to add or modify ===========================
@dataclass
class CookbookEntry:
    name: str


@dataclass
class RequiredItem:
    name: str
    quantity: int


@dataclass
class Recipe(CookbookEntry):
    required_items: List[RequiredItem]


@dataclass
class Ingredient(CookbookEntry):
    cook_time: int


# =============================================================================
# ==== HTTP Endpoint Stubs ====================================================
# =============================================================================
app = Flask(__name__)

# Store your recipes here!
cookbook = {}


# Task 1 helper (don't touch)
@app.route("/parse", methods=["POST"])
def parse():
    data = request.get_json()
    recipe_name = data.get("input", "")
    parsed_name = parse_handwriting(recipe_name)
    if parsed_name is None:
        return "Invalid recipe name", 400
    return jsonify({"msg": parsed_name}), 200


# [TASK 1] ====================================================================
# Takes in a recipeName and returns it in a form that
def parse_handwriting(recipeName: str) -> Union[str | None]:

    if recipeName is None:
        return None

    recipeName = re.sub(r"[-_]", " ", recipeName)  # 1
    recipeName = re.sub(r"[^a-zA-Z\s]", "", recipeName)  # 2
    recipeName = re.sub(r"\s+", " ", recipeName)  # 3
    recipeName = recipeName.strip().title()  # 4

    if len(recipeName) == 0:  # 5
        return None

    return recipeName


# [TASK 2] ====================================================================
# Endpoint that adds a CookbookEntry to your magical cookbook
@app.route("/entry", methods=["POST"])
def create_entry():
    data = request.get_json()

    if not data or "type" not in data or "name" not in data:
        return "check data", 400

    entry_type = data["type"]
    name = data["name"]

    if name in cookbook:
        return "entry names must be unique", 400

    if entry_type == "recipe":
        if "requiredItems" not in data:
            return "check data", 400

        required_items = []
        item_names = set()
        for item in data["requiredItems"]:
            if "name" not in item or "quantity" not in item:
                return "check data", 400
            if item["name"] in item_names:
                return "Recipe requiredItems can only have one element per name", 400
            item_names.add(item["name"])
            required_items.append(
                RequiredItem(name=item["name"], quantity=item["quantity"])
            )

        cookbook[name] = Recipe(name=name, required_items=required_items)

    elif entry_type == "ingredient":
        if "cookTime" not in data:
            return "check data", 400

        cook_time = data["cookTime"]
        if not isinstance(cook_time, int) or cook_time < 0:
            return "cookTime can only be greater than or equal to 0", 400

        cookbook[name] = Ingredient(name=name, cook_time=cook_time)

    else:
        return "type can only be recipe or ingredient", 400

    return "", 200


# [TASK 3] ====================================================================
# Endpoint that returns a summary of a recipe that corresponds to a query name
@app.route("/summary", methods=["GET"])
def summary():
    recipe_name = request.args.get("name")

    if not recipe_name or recipe_name not in cookbook:
        return "A recipe with the corresponding name cannot be found.", 400

    if not isinstance(cookbook[recipe_name], Recipe):
        return "The searched name is NOT a recipe name", 400

    try:
        ingredients, cook_time = get_ingredients_and_cook_time(recipe_name)

        summary = {
            "name": recipe_name,
            "cookTime": cook_time,
            "ingredients": [
                {"name": name, "quantity": quantity}
                for name, quantity in ingredients.items()
            ],
        }

        return jsonify(summary), 200
    except ValueError as e:
        return str(e), 400


def get_ingredients_and_cook_time(
    recipe_name: str, quantity: int = 1
) -> tuple[Dict[str, int], int]:
    # dictionary of ingredients and their quantities, and the total cook time.

    if recipe_name not in cookbook:
        raise ValueError("this name missing from cookbook") #should work 
    
    entry = cookbook[recipe_name]

    if isinstance(entry, Ingredient):
        return {recipe_name: quantity}, entry.cook_time * quantity

    if isinstance(entry, Recipe):
        total_ingredients = {}
        total_cook_time = 0

        for required_item in entry.required_items:
            base_ingredients, solo_cook_time = get_ingredients_and_cook_time(
                required_item.name, required_item.quantity * quantity
            )

            for ingredient, base_quantity in base_ingredients.items():
                total_ingredients[ingredient] = (
                    total_ingredients.get(ingredient, 0) + base_quantity
                )

            total_cook_time += solo_cook_time

        return total_ingredients, total_cook_time

    raise ValueError("check data")


# =============================================================================
# ==== DO NOT TOUCH ===========================================================
# =============================================================================

if __name__ == "__main__":
    app.run(debug=True, port=8080)
