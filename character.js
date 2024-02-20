
// JavaScript code to dynamically add character cards

// Function to create a new character card
function createCharacterCard(name) {
  // Create a new <div> element for the character card
  var card = document.createElement('div');
  card.classList.add('character-card');

  // Set the content of the character card
  card.innerHTML = '<h2>Name: ' + name + '</h2>';

  // Append the character card to the character container
  document.getElementById('character-container').appendChild(card);
}

// Function to handle the click event of the "Add Character" button
document.getElementById('add-character').addEventListener('click', function() {
  // Prompt the user to enter the name of the character
  var characterName = prompt('Enter the name of the character:');
  
  // If the user entered a name (not null or empty), create a new character card
  if (characterName) {
    createCharacterCard(characterName);
  }
});