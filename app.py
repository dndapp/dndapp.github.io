from flask import Flask, render_template, request
import requests
import os
import json

app = Flask(__name__)

# Dictionary to store character data for each character ID
character_data_dict = {}
# Dictionary to store encounter data
# Keys: Monster names, Values: Tuple (count, CR)
encounter = {}


# Function to calculate CON modifier based on CON score
def calculate_ability_modifier(con_score):
    if con_score in [2, 3]:
        return -4
    elif con_score in [4, 5]:
        return -3
    elif con_score in [6, 7]:
        return -2
    elif con_score in [8, 9]:
        return -1
    elif con_score in [10, 11]:
        return 0
    elif con_score in [12, 13]:
        return 1
    elif con_score in [14, 15]:
        return 2
    elif con_score in [16, 17]:
        return 3
    elif con_score in [18, 19]:
        return 4
    elif con_score in [20, 21]:
        return 5
    else:
        return None

# Calculate proficiency bonus
def calculate_prof(subclass_level):
    if subclass_level in [1,2,3,4]:
        return 2
    elif subclass_level in [5,6,7,8]:
        return 3
    elif subclass_level in [9,10,11,12]:
        return 4
    elif subclass_level in [13,14,15,16]:
        return 5
    elif subclass_level in [17,18,19,20]:
        return 6
    else:
        return None

def isEquippedArmor(item):
    itemdef = item.get('definition', {})
    if itemdef.get('filterType') is None: # This accounts for custom items that may not have the filterType set
        return False
    if "Armor" in itemdef.get('filterType') and itemdef.get('canEquip') is True:
        return True

def getInitMod(jobject,dex_mod,subclass_level):
    prof_mod = calculate_prof(subclass_level)
    initiative = 0
    modifiers = jobject.get('data', {}).get('modifiers',{})
    class_modifiers = modifiers.get('class',[])
    feat_modifiers = modifiers.get('feat',[])
    for cmod in class_modifiers:
        if "initiative" in cmod.get('subType'):
            if "half-proficiency" in cmod.get('type'):
                initiative += prof_mod//2
            elif cmod.get('value') is not None:
                initiative += cmod.get('value')
    for fmod in feat_modifiers:
        if "initiative" in fmod.get('subType'):
            initiative += fmod.get('value')
    initiative += dex_mod
    return initiative


# Function to fetch character data from D&D Beyond API
def fetch_character_data(character_id):
    url = f"https://character-service.dndbeyond.com/character/v5/character/{character_id}?includeCustomItems=true"
    response = requests.get(url)
    if response.status_code == 200:
        test = "TEST"
        character_data = response.json()
        # Determine CON
        con_score = character_data.get('data', {}).get('stats', [])[2].get('value')  # Extracting the CON score
        racial_mods = character_data.get('data', {}).get('modifiers', {}).get('race', [])
        for rmod in racial_mods: # Adjust CON score for racial modifiers
            rtype = rmod.get('subType')
            if "constitution-score" in rtype:
                con_score += rmod.get('value')
        feat_mods = character_data.get('data', {}).get('modifiers', {}).get('feat', [])
        for feat in feat_mods: #adjust CON score for feats
            ftype = feat.get('subType')
            if "constitution-score" in ftype:
                con_score += feat.get('value')
        con_modifier = calculate_ability_modifier(con_score)  # Calculating the CON modifier
        test = con_score

        # Get Class info
        highest_subclass_level = 0
        character_name = character_data.get('data', {}).get('name').split()[0]  # Extracting the character name
        base_hit_points = character_data.get('data', {}).get('baseHitPoints')  # Extracting the 'baseHitPoints' field
        removed_hit_points = character_data.get('data', {}).get('removedHitPoints', 0)  # Extracting removed hit points, default to 0 if not present
        classes_info = character_data.get('data', {}).get('classes', [])
        class_info_list = []
        total_levels = 0
        draconic_resilience = 0
        for class_info in classes_info:
            class_name = class_info.get('definition', {}).get('name')
            class_level = class_info.get('level')
            if class_level > highest_subclass_level:
                highest_subclass_level = class_level
            if class_name == "Sorcerer":
                ancestry = class_info.get('subclassDefinition', {}).get('name')
                if "Draconic Bloodline" in ancestry:
                    draconic_resilience = class_level # Accounts for sorcerers with Draconic Bloodline Ancestry
            class_info_list.append(f"{class_name} {class_level}")
            total_levels += class_level
        class_info = ', '.join(class_info_list)

        # Calculate current and maximum HP (Hit Points)
        feats = character_data.get('data', {}).get('feats', [])
        tough = 0
        for feat in feats:
            if "Tough" in feat.get('definition', {}).get('name'):
                tough = 2 * total_levels
        con_modifier = calculate_ability_modifier(con_score)
        total_added_hp = con_modifier * total_levels
        temporary_hp = character_data.get('data', {}).get('temporaryHitPoints')
        max_hp = base_hit_points + total_added_hp + draconic_resilience + temporary_hp + tough
        current_hp = max_hp - removed_hit_points

        # Grab Avatar Image
        avatar_url = character_data.get('data', {}).get('decorations', {}).get('avatarUrl', '')

        # Calculate AC
        # First determine dex modifier
        dex_score = character_data.get('data', {}).get('stats', [])[1].get('value')  # Extracting the DEX score
        racial_mods = character_data.get('data', {}).get('modifiers', {}).get('race', [])
        for rmod in racial_mods: # Adjust DEX score for racial modifiers
            rtype = rmod.get('subType')
            if "dexterity-score" in rtype:
                dex_score += rmod.get('value')
        feat_mods = character_data.get('data', {}).get('modifiers', {}).get('feat', [])
        for feat in feat_mods: #adjust DEX score for feats
            ftype = feat.get('subType')
            if "dexterity-score" in ftype:
                dex_score += feat.get('value')
        dex_modifier = calculate_ability_modifier(dex_score)  # Calculating the DEX modifier

        inventory = character_data.get('data', {}).get('inventory', [])
        armorclass = 0
        for item in inventory:
            if isEquippedArmor(item):
                itemdef = item.get('definition', {})
                armortype = itemdef.get('armorTypeId')
                if armortype <= 2:
                    armorclass += itemdef.get('armorClass') + dex_modifier
                else:
                    armorclass += itemdef.get('armorClass')
        if armorclass == 0:
            armorclass = 10 + dex_modifier

        test = armorclass
        class_mods = character_data.get('data', {}).get('modifiers', {}).get('class', [])
        for class_mod in class_mods:
            ctype = class_mod.get('subType')
            cgranted = class_mod.get('isGranted') # Check to make sure that the benefit is active
            if "armored-armor-class" in ctype and cgranted: #This also catches "unarmored-armor-class" situations
                armorclass += class_mod.get('value')

        # Initiative calculations
        initiative_mod = getInitMod(character_data, dex_modifier, highest_subclass_level)
        return character_name, current_hp, max_hp, class_info, avatar_url, armorclass, initiative_mod, test
    else:
        print("ERROR")
        return 1,2,3,4,5,6,7,response.status_code
        #return None, None, None, None, None, None, None, "ERROR"



# Define the directory path where your JSON files are stored
BESTIARY_DIRECTORY = 'data/bestiary'

# Function to load all JSON files from the bestiary directory
def load_bestiary_data():
    bestiary_data = {}

    # Iterate through all files in the bestiary directory
    for filename in os.listdir(BESTIARY_DIRECTORY):
        if filename.startswith('bestiary') and filename.endswith('.json'):
            file_path = os.path.join(BESTIARY_DIRECTORY, filename)

            # Read the JSON file and load its contents into the bestiary_data dictionary
            with open(file_path, 'r') as file:
                bestiary_json = json.load(file)['monster']

            # Organize the data by monster name or prefix
            for monster in bestiary_json:
                monster_name = monster['name']
                #print(monster_name)
                bestiary_data[monster_name] = monster

    return bestiary_data

# Load the bestiary data when the application starts
bestiary_data = load_bestiary_data()

lastsearch = []
lastquery = ""

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query', '').strip()
    results = []

    if query:
        # Iterate through the bestiary data to find matching monsters
        for monster_name in bestiary_data.keys():
            if query.lower() in monster_name.lower():
                #results.append(monster_name)
                results.append(bestiary_data[monster_name])
    print(results)
    print(query)
    lastsearch = list(results)
    lastquery = str(query)

    return render_template('index.html', query=query, results=results, character_data_dict=character_data_dict, bestiary_data=bestiary_data)



### TEMP DEBUG CODE ###
# This code helps by preloading IDs so I don't have to manually enter them every time.
characterIds = ['115856846', '116749173', '115921528', '115304142', '115857640', '116751694', '117834166']
for cid in characterIds:
    character_name, current_hp, max_hp, class_info, avatar_url, armorclass, initiative_mod, test = fetch_character_data(cid)
    character_data_dict[cid] = {'name': character_name, 'current_hp': current_hp, 'max_hp': max_hp, 'class_info': class_info, 'avatar_url': avatar_url, 'armorclass': armorclass, 'initiative_mod': initiative_mod, 'test':test}
### TEMP DEBUG CODE ###


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        character_id_input = request.form.get('character_id')
        # Fetch character data from D&D Beyond API
        character_name, current_hp, max_hp, class_info, avatar_url, armorclass, initiative_mod, test = fetch_character_data(character_id_input)

        values = [character_name, current_hp, max_hp, class_info, avatar_url, armorclass, initiative_mod, test]
        for item in values:
            if item is None:
                return render_template('index.html', character_data_dict=character_data_dict, bestiary_data=bestiary_data, encounter=encounter)
        
        # Store character data in the dictionary
        character_data_dict[character_id_input] = {'name': character_name, 'current_hp': current_hp, 'max_hp': max_hp, 'class_info': class_info, 'avatar_url': avatar_url, 'armorclass': armorclass, 'initiative_mod': initiative_mod, 'test':test}

    return render_template('index.html', character_data_dict=character_data_dict, bestiary_data=bestiary_data, encounter=encounter)


@app.route('/add_to_encounter', methods=['POST'])
def add_to_encounter():
    monster_name = request.form.get('monster_name')
    cr = eval(request.form.get('cr'))
    #cr = float(request.form.get('cr'))

    # Add monster to the encounter or update its count and CR
    if monster_name in encounter:
        count, total_cr = encounter[monster_name]
        encounter[monster_name] = (count + 1, total_cr + cr)
    else:
        encounter[monster_name] = (1, cr)

    print(lastsearch)
    print(lastquery)
    return render_template('index.html', character_data_dict=character_data_dict, bestiary_data=bestiary_data, encounter=encounter, results=lastsearch, query=lastquery)

@app.route('/remove_from_encounter', methods=['POST'])
def remove_from_encounter():
    monster_name = request.form.get('monster_name')
    cr = eval(request.form.get('cr'))

    # Remove monster from the encounter or update its count and CR
    if monster_name in encounter:
        count, total_cr = encounter[monster_name]
        if count == 1:
            del encounter[monster_name]
        else:
            encounter[monster_name] = (count - 1, total_cr - cr)

    return render_template('index.html', character_data_dict=character_data_dict, bestiary_data=bestiary_data, encounter=encounter, results=lastsearch, query=lastquery)

if __name__ == '__main__':
    app.run(debug=True)
