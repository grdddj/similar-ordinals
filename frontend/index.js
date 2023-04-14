function selectImage() {
  const input = document.getElementById('fileInput');
  input.click();
  input.addEventListener('change', () => {
    const file = input.files[0];
    const fileNameDisplay = document.getElementById('fileName');
    fileNameDisplay.innerHTML = `File Name: ${file.name}`;
    const filenameAndSubmit = document.getElementById('filenameAndSubmit');
    filenameAndSubmit.style.display = "block";
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
      console.log(data)
      // Hide the loading popup and submit button
      popup.style.display = "none";
      const filenameAndSubmit = document.getElementById('filenameAndSubmit');
      filenameAndSubmit.style.display = "none";
      // Show the results
      updateResults(data);
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


function updateResults(new_data) {
  // Load everything into dictionary for faster lookup per ID
  const resultDict = {};
  console.log(new_data)
  new_data.result.forEach(function (item) {
    resultDict[item.id] = item;
  });

  let output = '';

  new_data.result.forEach(function (item) {
    output += `<div class="card" ord-id="${item.id}">
                 <img src="${item.hiro_content_link}">
                 <button class="id-btn">Ordinal ID: ${item.id}</button>
                 <p><strong>Similarity:</strong>${item.similarity}</p>
               </div>`;
  });

  const resultDiv = document.getElementById('result');
  resultDiv.innerHTML = output;
  const resultsDivOverall = document.getElementById('results');
  resultsDivOverall.style.display = "block";

  const divCards = document.querySelectorAll('.card');
  const popupContainer = document.getElementById('popup-container');
  const popupDetails = document.getElementById('popupDetails');

  // Open details by clicking on each card
  divCards.forEach(function (cardDiv) {
    cardDiv.addEventListener('click', function () {
      const ordId = cardDiv.getAttribute('ord-id');
      const item = resultDict[ordId]
      const mintedAddressLink = `https://mempool.space/address/${item.minted_address}`

      const content = `
        <div id="popup-content-details">
          <span id="close-btn">&times;</span>

          <div class="popup-details">
            <p><strong>ID:</strong> ${ordId}</p>
            <p><strong>Time Published:</strong> ${item.datetime}</p>
            <p><strong>Content type:</strong> ${item.content_type}</p>
            <p><strong>Content length:</strong> ${item.content_length} bytes</p>
            <p><strong>Minted Address:</strong> <a href="${mintedAddressLink}" target="_blank">${item.minted_address}</a></p>
            <p><strong>Ordinals.com link:</strong> <a href="${item.ordinals_com_link}" target="_blank">${item.ordinals_com_link}</a></p>
            <p><strong>Transaction ID:</strong> <a href="${item.mempool_space_link}" target="_blank">${item.tx_id}</a></p>
          </div>
        </div>
      `;

      popupDetails.innerHTML = content;
      popupContainer.style.display = 'flex';

      const closeBtn = document.getElementById('close-btn');
      closeBtn.addEventListener('click', function () {
        popupContainer.style.display = 'none';
      });
    });
  });
}
