import json

# Replace 'your_file.json' with the actual file name or path to your JSON file
input_file_path = r'data\2023-09-26\games_Bet365Webscraper.json'
# Replace 'formatted_file.json' with the desired name or path for the new formatted JSON file
output_file_path = 'formatted_file.json'

# Read the file and load the JSON
with open(input_file_path, 'r') as file:
    data = json.load(file)

# Write the formatted JSON to a new file with indentation
with open(output_file_path, 'w') as file:
    json.dump(data, file, indent=4, ensure_ascii=False)
