document.addEventListener('DOMContentLoaded', function() {
    const resultDiv = document.getElementById('result');
    const result = localStorage.getItem('resultData');
    resultDiv.innerHTML = result;
  });