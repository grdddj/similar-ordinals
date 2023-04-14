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
  
    // Show the loading popup
    const popup = document.getElementById('loadingPopup');
    popup.style.display = "block";
  
    fetch('http://grdddj.eu:8001/file', {
      method: 'POST',
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      const result = JSON.stringify(data);
      localStorage.setItem('resultData', result);
      // Hide the loading popup
      popup.style.display = "none";
      // Show the success popup
      
      // Redirect to results page after a delay
      setTimeout(function() {
        window.location.href = "results.html";
      }, 500);
    })
    .catch(error => {
      console.error(error);
      // Hide the loading popup
      popup.style.display = "none";
      // Show the error popup
      const errorPopup = document.getElementById('errorPopup');
      errorPopup.style.display = "block";
    });
  }
  