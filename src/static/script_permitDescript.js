/*
Name: script_permitDescript.js
 Description: Handles permit data storage and modal behavior for displaying parking permit details. Includes formatting of descriptions and user interaction logic for opening/closing modals.
Programmers: Evans Chigweshe
Creation Date: 03/28/2026
Preconditions: HTML must contain modal elements with ID (modal, modal-title, modal-description).
Postconditions: Displays permit details dynamically in modal.
Errors/Exceptions: No known errors.
Side Effects: Updates DOM elements and UI visibility.
Invariants: permitData structure remains consistent.
*/




// PERMIT DATA OBJECT stores all permit titles and descriptions. Descriptions use '\n' for line separation 
const permitData = {
  red: {
    title: "Red Permit",
    description: "Allows parking in Red-designated lots across campus.\nAlso valid in all Yellow, and University Housing lots, except Alumni Place."
  },
  blue: {
    title: "Blue Permit",
    description: "Allows parking in Blue-designated lots across campus.\nAlso valid in all Red, Yellow, and University Housing lots, except Alumni Place."
  },
  yellow: {
    title: "Yellow Permit",
    description: "Allows parking in Yellow-designated lots across campus.\nVisitors may pay by space to park in yellow zones on campus.\nNote: It's open to parking without a permit when classes are not in session."
  },
  green: {
    title: "Green Permit",
    description: "Residential parking for students living on campus."
  },
  gold: {
    title: "Gold Permit",
    description: "Premium parking option for faculty/staff with access to high-demand lots.\nValid in all Gold, Blue, Red, Yellow, and University Housing lots, except Alumni Place."
  },
  orange: {
    title: "Orange Permit",
    description: "A specified housing permit for Naismith Hall.\nAlso valid in yellow zones during summer."
  },
  fuchsia: {
    title: "Fuchsia Permit",
    description: "A specified housing permit for Hawker Apartments.\nAlso valid in yellow zones during summer."
  },
  brown: {
    title: "Brown Permit",
    description: "A specified housing permit for Scholarship Halls.\nAlso valid in yellow zones during summer."
  },
  allen: {
    title: "Allen Fieldhouse Garage",
    description: "Garage parking near Allen Fieldhouse. Issued on annual basis only.\nNot valid for parking during home basketball games.\nNot valid in lots 6, 7, 8, 17, 35, 41, 54, 70, 71, 72, 90, 109, 110, 125, 127, 129, or the Mississippi Street or Central District garages.\nAny current permit is valid in the garage from 5pm until 7am Monday-Friday and 24 hours on weekends except during posted event restrictions."
  },
  central: {
    title: "Central District Garage",
    description: "Central campus garage with convenient access to academic buildings and housing.\nNot valid for parking during home basketball games.\nGarage permits not valid in lots 6, 7, 20, 31, 41, 54, 70, 71, 72, 90, 93, 109, 110, 112, 113, 114, 116, 119, 125, 127, and 129, or the Mississippi Street or Allen Fieldhouse garages.\nAny current permit is valid in the garage from 5pm until 7am Monday-Friday and 24 hours on weekends except during posted event restrictions."
  },
  mississippi: {
    title: "Mississippi Street Garage",
    description: "Garage located along Mississippi Street providing structured parking for campus users. \nNot valid for parking during home football games and other special events.\nNot valid in lots 16, 39, 53, 91, 92, 94, or the Allen Fieldhouse or Central District garages.\nAny current permit is valid in the garage from 5pm until 7am Monday-Friday and 24 hours on weekends except during posted event restrictions."
  }
};


// formatDescription converts newline-separated text into bullet points for display in HTML
function formatDescription(text) {
  return text
    .split('\n')   // Split text into lines
    .map(line => `• ${line.trim()}`) // Add bullet to each line
    .join('<br>');       // Join with HTML line breaks
}


// openModel displays modal with selected permit information
function openModal(type) {
  document.getElementById("modal-title").innerText = permitData[type].title;
  document.getElementById("modal-description").innerHTML =
    formatDescription(permitData[type].description);
  document.getElementById("modal").style.display = "block";
}

//  CloseModel hides the modal when user clicks close button
function closeModal() {
  document.getElementById("modal").style.display = "none";
}


// WINDOW CLICK HANDLER closes modal when user clicks outside of modal content
window.onclick = function(event) {
  const modal = document.getElementById("modal");
  if (event.target === modal) {
    modal.style.display = "none";
  }
}