function selectImage() {
    const input = document.getElementById('fileInput');
    input.click();
    input.addEventListener('change', () => {
      const file = input.files[0];
      const fileNameDisplay = document.getElementById('fileName');
      fileNameDisplay.innerHTML = `File Name: ${file.name}`;
      const submitButton = document.getElementById('submitButton');
      submitButton.style.display = "block";
    });
  }
  
  function submitImage() {
    const input = document.getElementById('fileInput');
    const file = input.files[0];
    const formData = new FormData();
    formData.append('file', file);
  
    fetch('http://grdddj.eu:8001/file', {
      method: 'POST',
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      const result = JSON.stringify(data);
      localStorage.setItem('resultData', result);
      window.location.href = "results.html";
    })
    .catch(error => console.error(error));
  }
  
  
  const uploadButton = document.getElementById('uploadButton');
  uploadButton.addEventListener('click', selectImage);
  
  const submitButton = document.getElementById('submitButton');
  submitButton.addEventListener('click', submitImage);
  