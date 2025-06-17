document.getElementById('post-selector').addEventListener('change', function() {
    const newPostId = this.value;
    window.location.search = '?post_id=' + newPostId;
});

document.getElementById('runLLM').addEventListener('click', function() {
    const input = document.getElementById('inputValue').value;
    const systemPrompt = document.getElementById('systemPrompt').value;
    const taskPrompt = document.getElementById('taskPrompt').value;
    const model = document.getElementById('model').value;
    const temperature = document.getElementById('temperature').value;
    const output = `\n[System]\n${systemPrompt}\n\n[Task]\n${taskPrompt.replace('{{ idea_seed }}', input)}\n\n[Model: ${model}, Temp: ${temperature}]\n\n(This is a placeholder. No real LLM call yet.)`;
    document.getElementById('outputValue').value = output;
});

function populateFieldDropdowns() {
    const postDevFields = window.postDevFields || {};
    const inputField = document.getElementById('inputField');
    const outputField = document.getElementById('outputField');
    inputField.innerHTML = '';
    outputField.innerHTML = '';
    Object.keys(postDevFields).forEach(field => {
        const opt1 = document.createElement('option');
        opt1.value = field;
        opt1.textContent = field;
        inputField.appendChild(opt1);
        const opt2 = document.createElement('option');
        opt2.value = field;
        opt2.textContent = field;
        outputField.appendChild(opt2);
    });
}

function updateInputValue() {
    const postDevFields = window.postDevFields || {};
    const inputField = document.getElementById('inputField');
    const inputValue = document.getElementById('inputValue');
    inputValue.value = postDevFields[inputField.value] || '';
}

function updateOutputValue() {
    const postDevFields = window.postDevFields || {};
    const outputField = document.getElementById('outputField');
    const outputValue = document.getElementById('outputValue');
    outputValue.value = postDevFields[outputField.value] || '';
}

document.addEventListener('DOMContentLoaded', function() {
    populateFieldDropdowns();
    updateInputValue();
    updateOutputValue();
    document.getElementById('inputField').addEventListener('change', updateInputValue);
    document.getElementById('outputField').addEventListener('change', updateOutputValue);
}); 