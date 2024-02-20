// Function to create a new character card
function createCharacterCard(id) {
    // Fetch character data from the provided URL
    fetch(`https://character-service.dndbeyond.com/character/v5/character/${id}?includeCustomItems=true`)
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      console.log(data);
      .then(data => {
        // Create a new <div> element for the character card
        var card = document.createElement('div');
        card.classList.add('character-card');
  
        // Set the content of the character card using the fetched data
        card.innerHTML = `
          <h2>Name: ${data.id}</h2>
          <!-- Add more properties as needed -->
        `;
  
        // Append the character card to the character container
        document.getElementById('character-container').appendChild(card);
      })
      .catch(error => {
        console.error('Error fetching character data:', error);
      });
  }
  
  // Function to handle the click event of the "Add Character" button
  document.getElementById('add-character').addEventListener('click', function() {
    // Prompt the user to enter the ID number of the character
    var characterID = prompt('Enter the ID number of the character:');
    
    // If the user entered an ID number (not null or empty), create a new character card
    if (characterID) {
      createCharacterCard(characterID);
    }
  });