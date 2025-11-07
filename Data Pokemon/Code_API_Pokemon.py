import requests
import pandas as pd

# URL base de la PokeAPI
base_url = "https://pokeapi.co/api/v2/pokemon/"

# Función para formatear ID con ceros a la izquierda
def format_pokemon_id(pokemon_id):
    return f"{pokemon_id:03}"

# Función para obtener habilidades
def fetch_pokemon_abilities(data, pokemon_id, pokemon_name):
    abilities = []
    for ability_entry in data["abilities"]:
        ability_name = ability_entry["ability"]["name"]
        hidden = ability_entry["is_hidden"]
        ability_id = ability_entry["ability"]["url"].split("/")[-2]
        ability_url = ability_entry["ability"]["url"]
        effect, short_effect = fetch_ability_details(ability_url)
        abilities.append({
            "Pokemon ID": format_pokemon_id(pokemon_id),
            "Ability ID": format_pokemon_id(int(ability_id)),
            "Ability": ability_name,
            "Hidden Ability": hidden,
            "Effect": short_effect
        })
    return abilities

# Función para obtener la descripción de una habilidad
def fetch_ability_details(ability_url):
    response = requests.get(ability_url)
    if response.status_code == 200:
        data = response.json()
        effect = next(
            (entry["effect"] for entry in data["effect_entries"] if entry["language"]["name"] == "en"),
            "No effect description available"
        )
        short_effect = next(
            (entry["short_effect"] for entry in data["effect_entries"] if entry["language"]["name"] == "en"),
            "No short effect available"
        )
        return effect, short_effect
    else:
        return "Unknown", "Unknown"

# Función para obtener ubicaciones
def fetch_pokemon_locations(pokemon_id, pokemon_name):
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}/encounters"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        locations = []
        for location in data:
            location_name = location["location_area"]["name"].replace("-", " ").title()
            for version in location["version_details"]:
                version_name = version["version"]["name"].capitalize()
                locations.append({
                    "Pokemon ID": format_pokemon_id(pokemon_id),
                    "Pokemon": pokemon_name,
                    "Location": location_name,
                    "Version": version_name
                })
        return locations
    else:
        return []

# Función para obtener movimientos
def fetch_pokemon_moves(data, pokemon_id):
    moves = []
    for move_entry in data["moves"]:
        move_name = move_entry["move"]["name"]
        for detail in move_entry["version_group_details"]:
            method = detail["move_learn_method"]["name"]
            level = detail["level_learned_at"]
            moves.append({
                "Pokemon ID": format_pokemon_id(pokemon_id),
                "Move": move_name,
                "Method": method.capitalize(),
                "Level": level if method == "level-up" else "N/A"
            })
    moves_df = pd.DataFrame(moves)
    unique_moves = moves_df.drop_duplicates(subset=["Pokemon ID", "Move", "Method", "Level"])
    return unique_moves.to_dict("records")

# Función para obtener evoluciones
def fetch_evolution_chain(species_url):
    species_response = requests.get(species_url)
    if species_response.status_code == 200:
        species_data = species_response.json()
        evolution_chain_url = species_data["evolution_chain"]["url"]
        evolution_response = requests.get(evolution_chain_url)
        if evolution_response.status_code == 200:
            evolution_data = evolution_response.json()
            chain = evolution_data["chain"]
            evolutions = []
            current = chain
            while current:
                parent = current["species"]["name"]
                parent_id = current["species"]["url"].split("/")[-2]
                for evolution in current["evolves_to"]:
                    child = evolution["species"]["name"]
                    child_id = evolution["species"]["url"].split("/")[-2]
                    level_details = evolution["evolution_details"][0] if evolution["evolution_details"] else {}
                    level = level_details.get("min_level", "Unknown")
                    evolutions.append({
                        "Parent": parent,
                        "Parent ID": format_pokemon_id(int(parent_id)),
                        "Child": child,
                        "Child ID": format_pokemon_id(int(child_id)),
                        "Level": level
                    })
                current = current["evolves_to"][0] if current["evolves_to"] else None
            evolutions_df = pd.DataFrame(evolutions)
            unique_evolutions = evolutions_df.drop_duplicates(subset=["Parent", "Child", "Level"])
            return unique_evolutions.to_dict("records")
    return []

# Función para obtener la tabla principal
def fetch_pokemon_main(data, pokemon_id, species_data):
    stats = {stat["stat"]["name"]: stat["base_stat"] for stat in data["stats"]}
    gender_rate = species_data["gender_rate"]
    gender = "Genderless" if gender_rate == -1 else f"{(8 - gender_rate) / 8 * 100:.1f}% male, {gender_rate / 8 * 100:.1f}% female"
    return {
        "Pokemon ID": format_pokemon_id(pokemon_id),
        "Name": data["name"],
        "Description": next(
            (entry["flavor_text"] for entry in species_data["flavor_text_entries"] if entry["language"]["name"] == "en"),
            "No description available"
        ),
        "Types": ", ".join([t["type"]["name"] for t in data["types"]]),
        "Gender": gender,
        "HP": stats.get("hp", 0),
        "Attack": stats.get("attack", 0),
        "Defense": stats.get("defense", 0),
        "Special Attack": stats.get("special-attack", 0),
        "Special Defense": stats.get("special-defense", 0),
        "Speed": stats.get("speed", 0),
        "Weight": data["weight"],
        "Height": data["height"],
        "Base Experience": data["base_experience"]
    }

# Listas para almacenar datos
pokemon_main_list = []
abilities_list = []
locations_list = []
moves_list = []
evolutions_list = []

# Función principal para obtener todos los datos
def fetch_all_pokemon(limit=151):
    for pokemon_id in range(1, limit + 1):
        url = f"{base_url}{pokemon_id}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            species_url = data["species"]["url"]
            species_response = requests.get(species_url)
            if species_response.status_code == 200:
                species_data = species_response.json()
                pokemon_main_list.append(fetch_pokemon_main(data, pokemon_id, species_data))
                abilities_list.extend(fetch_pokemon_abilities(data, pokemon_id, data["name"]))
                locations_list.extend(fetch_pokemon_locations(pokemon_id, data["name"]))
                moves_list.extend(fetch_pokemon_moves(data, pokemon_id))
                evolutions_list.extend(fetch_evolution_chain(species_url))

# Ejecutar la extracción de datos
fetch_all_pokemon(limit=151)

# Crear DataFrames
pokemon_main_df = pd.DataFrame(pokemon_main_list)
abilities_df = pd.DataFrame(abilities_list)
locations_df = pd.DataFrame(locations_list)
moves_df = pd.DataFrame(moves_list)
evolutions_df = pd.DataFrame(evolutions_list)

# Guardar en un archivo Excel
file_path = "pokemon_data_gen1_complete.xlsx"  # Cambia la ruta si deseas guardar en otro lugar
with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
    pokemon_main_df.to_excel(writer, sheet_name="Pokemon", index=False)
    abilities_df.to_excel(writer, sheet_name="Abilities", index=False)
    locations_df.to_excel(writer, sheet_name="Locations", index=False)
    moves_df.to_excel(writer, sheet_name="Moves", index=False)
    evolutions_df.to_excel(writer, sheet_name="Evolutions", index=False)

print(f"Archivo '{file_path}' generado exitosamente.")
