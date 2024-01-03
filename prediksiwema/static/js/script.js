const fileInput = document.getElementById('datasetFile');
const fileNameText = document.getElementById('fileName');
const dropZone = document.getElementById('dropZone');

fileInput.addEventListener('change', handleFileSelect);
dropZone.addEventListener('dragover', handleDragOver);
dropZone.addEventListener('dragleave', handleDragLeave);
dropZone.addEventListener('drop', handleFileDrop);

function handleFileSelect(event) {
  const file = event.target.files[0];
  displayFileName(file.name);
}

function handleDragOver(event) {
  event.preventDefault();
  dropZone.classList.add('dragover');
}

function handleDragLeave(event) {
  event.preventDefault();
  dropZone.classList.remove('dragover');
}

function handleFileDrop(event) {
  event.preventDefault();
  dropZone.classList.remove('dragover');
  const file = event.dataTransfer.files[0];
  displayFileName(file.name);
}

function displayFileName(name) {
  fileNameText.textContent = name;
}
