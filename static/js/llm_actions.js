document.getElementById('runLLM').addEventListener('click', function() {
    const input = document.getElementById('inputValue').value;
    const systemPrompt = document.getElementById('systemPrompt').value;
    const taskPrompt = document.getElementById('taskPrompt').value;
    const model = document.getElementById('model').value;
    const temperature = document.getElementById('temperature').value;
    const output = `\n[System]\n${systemPrompt}\n\n[Task]\n${taskPrompt.replace('{{ idea_seed }}', input)}\n\n[Model: ${model}, Temp: ${temperature}]\n\n(This is a placeholder. No real LLM call yet.)`;
    document.getElementById('outputValue').value = output;
}); 