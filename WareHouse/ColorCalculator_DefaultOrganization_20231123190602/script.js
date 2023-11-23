/*
Initializes calculator buttons and attaches event listeners for user interaction.
*/
// Function to initialize the calculator's buttons.
function initializeButtons() {
    const buttonsContainer = document.getElementById('buttons');
    const buttonValues = [
        '7', '8', '9', '+',
        '4', '5', '6', '-',
        '1', '2', '3', '*',
        'C', '0', '=', '/'
    ];
    const colors = ['red', 'green', 'blue', 'yellow']; // Colors for the buttons
    buttonValues.forEach((value, index) => {
        const button = document.createElement('button');
        button.textContent = value;
        button.classList.add('button', colors[index % colors.length]);
        button.classList.add(isNaN(value) && value !== '.' ? 'action' : 'number');
        buttonsContainer.appendChild(button);
    });
}
// Function to attach event listeners to the buttons.
function attachEventListeners() {
    const numberButtons = document.querySelectorAll('.number');
    const actionButtons = document.querySelectorAll('.action');
    const display = document.getElementById('display');
    numberButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            handleNumberClick(event, display);
        });
    });
    actionButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            handleActionClick(event, display);
        });
    });
}
// Function to update the display with the clicked number or action.
function updateDisplay(display, value) {
    display.value += value;
}
// Function to evaluate the mathematical expression entered by the user.
function calculate(expression) {
    try {
        // Use math.js for safe expression evaluation
        return math.evaluate(expression);
    } catch (error) {
        return 'Error';
    }
}
// Event handler for number button clicks.
function handleNumberClick(event, display) {
    const value = event.target.textContent;
    updateDisplay(display, value);
}
// Event handler for action button clicks.
function handleActionClick(event, display) {
    const value = event.target.textContent;
    if (value === '=') {
        display.value = calculate(display.value);
    } else if (value === 'C') {
        display.value = '';
    } else {
        updateDisplay(display, value);
    }
}
// Initialization of the calculator once the DOM content has fully loaded.
document.addEventListener("DOMContentLoaded", function() {
    initializeButtons();
    attachEventListeners();
});