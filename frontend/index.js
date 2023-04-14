const SPONSOR_MINTING_WEBSITE = "https://ordinalswallet.com/inscribe"

function selectImage() {
  const input = document.getElementById('fileInput');
  input.click();
  input.addEventListener('change', () => {
    const file = input.files[0];
    // Showing the chosen picture in a card
    const reader = new FileReader();
    reader.addEventListener('load', (event) => {
      fill_chosen_picture(event.target.result, null);
    });
    reader.readAsDataURL(file);
    // Submitting the image
    submitImage();
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
      // Hide the loading popup
      popup.style.display = "none";
      // Show the results
      updateResults(data, null);
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

function chooseOrdID() {
  const ordID = prompt("Please enter the Ordinal ID:");

  // Show the loading popup
  const popup = document.getElementById('loadingPopup');
  popup.style.display = "block";

  fetch('http://grdddj.eu:8001/ord_id/' + ordID)
    .then(response => response.json())
    .then(data => {
      // Hide the loading popup
      popup.style.display = "none";
      if (data.result.length == 0) {
        alert("Given Ordinal ID is not a picture.");
        return;
      }
      // Show the results
      updateResults(data, ordID);
      // Show the chosen picture
      const chosenItem = data.result.find(item => item.id == ordID);
      if (chosenItem) {
        fill_chosen_picture(chosenItem.hiro_content_link, ordID);
      }
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

function fill_chosen_picture(src, ord_id) {
  const chosenPic = document.getElementById('chosen-picture');
  let firstLine = '';
  let secondLine = '';
  if (ord_id) {
    firstLine = `Your ordinal: ${ord_id}`;
  } else {
    firstLine = 'Your potential ordinal';
    secondLine = `Mint <a href=${SPONSOR_MINTING_WEBSITE} target="_blank">HERE</a>`;
  }
  chosenPic.innerHTML = `<div class="card">
                 <img src="${src}">
                 <p><strong>${firstLine}</strong></p>
                 <p>${secondLine}</p>
               </div>`;
}


function updateResults(new_data, chosenOrdID) {
  // Load everything into dictionary for faster lookup per ID
  const resultDict = {};
  new_data.result.forEach(function (item) {
    resultDict[item.id] = item;
  });

  let output = '';

  new_data.result.forEach(function (item) {
    // Not displaying the item which user chose - by ordID
    // Also, marking those pixel-perfect matches as those
    let isDuplicate = false;
    if (chosenOrdID) {
      const chosenItem = resultDict[chosenOrdID];
      if (item.id == chosenOrdID) {
        return;
      } else if (item.content_hash == chosenItem.content_hash) {
        isDuplicate = true;
      }
    }
    
    let similarity = item.similarity;
    let red = '';
    if (isDuplicate) {
      similarity = "IDENTICAL";
      red = 'style="background-color: red"';
    }
    
    output += `<div class="card" ${red} ord-id="${item.id}">
                 <img src="${item.hiro_content_link}">
                 <button class="id-btn">Ordinal ID: ${item.id}</button>
                 <p><strong>Similarity: </strong>${similarity}</p>
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
