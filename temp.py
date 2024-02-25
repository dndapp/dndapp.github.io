from flask import Flask, render_template, request
import requests

app = Flask(__name__)

# Dictionary to store character data for each character ID
character_data_dict = {}

# Function to calculate CON modifier based on CON score
def calculate_con_modifier(con_score):
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

# Function to fetch character data from D&D Beyond API
def fetch_character_data(character_id):
    url = f"https://character-service.dndbeyond.com/character/v5/character/{character_id}?includeCustomItems=true"
    response = requests.get(url)
    if response.status_code == 200:
        character_data = response.json()
        




        character_name = character_data.get('data', {}).get('name')  # Extracting the character name
        base_hit_points = character_data.get('data', {}).get('baseHitPoints')  # Extracting the 'baseHitPoints' field
        removed_hit_points = character_data.get('data', {}).get('removedHitPoints', 0)  # Extracting removed hit points, default to 0 if not present
        temp_hit_points = character_data.get('data', {}).get('temporaryHitPoints', 0)  # Extracting temporary hit points, default to 0 if not present
        con_score = character_data.get('data', {}).get('stats', [])[2].get('value')  # Extracting the CON score
        con_modifier = calculate_con_modifier(con_score)  # Calculating the CON modifier
        classes_info = character_data.get('data', {}).get('classes', [])
        class_info_list = []
        total_levels = 0
        for class_info in classes_info:
            class_name = class_info.get('definition', {}).get('name')
            class_level = class_info.get('level')
            class_info_list.append(f"{class_name} {class_level}")
            total_levels += class_level
        class_info = ', '.join(class_info_list)
        # Calculate current and maximum HP (Hit Points)
        con_modifier = calculate_con_modifier(con_score)
        total_added_hp = con_modifier * total_levels
        max_hp = base_hit_points + total_added_hp + temp_hit_points
        current_hp = max_hp - removed_hit_points
        # Extracting the character card image URL
        avatar_url = character_data.get('data', {}).get('decorations', {}).get('avatarUrl', '')
        return character_name, current_hp, max_hp, class_info, avatar_url
    else:
        return None, None, None, None, None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        character_id_input = request.form.get('character_id')
        # Fetch character data from D&D Beyond API
        character_name, current_hp, max_hp, class_info, avatar_url = fetch_character_data(character_id_input)
        if all([character_name, current_hp, max_hp, class_info, avatar_url]):
            # Store character data in the dictionary
            character_data_dict[character_id_input] = {'name': character_name, 'current_hp': current_hp, 'max_hp': max_hp, 'class_info': class_info, 'avatar_url': avatar_url}

    return render_template('index.html', character_data_dict=character_data_dict)

if __name__ == '__main__':
    app.run(debug=True)
