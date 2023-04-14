const SPONSOR_MINTING_WEBSITE = "https://ordinalswallet.com/inscribe";

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

    fetch('https://api.ordsimilarity.com/file', {
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
        });
}

function chooseOrdID() {
    const ordID = prompt("Please enter the Ordinal ID:");

    // User cancelled the prompt or entered nothing
    if (ordID == null || ordID == "") {
        return;
    }

    fetch('https://api.ordsimilarity.com/ord_id/' + ordID)
        .then(response => response.json())
        .then(data => {
            if (data.result.length == 0) {
                alert("Given Ordinal ID is not a picture.");
                return;
            }
            // Show the results
            updateResults(data, ordID);
            // Show the chosen picture
            const chosenItem = data.result.find(item => item.id == ordID);
            if (chosenItem) {
                fill_chosen_picture(chosenItem.hiro_content_link, chosenItem);
            }
        })
        .catch(error => {
            console.error(error);
            alert("Error when getting data. We apologize, please try later.");
        });
}

function fill_chosen_picture(src, chosenItem) {
    const chosenPic = document.getElementById('chosen-picture');
    let firstLine = '';
    let secondLine = '';
    if (chosenItem) {
        firstLine = `Your ordinal`;
        secondLine = chosenItem.id;
    } else {
        firstLine = 'Your Potential Ordinal';
        secondLine = `Mint <a href=${SPONSOR_MINTING_WEBSITE} target="_blank">Here</a>`;
    }

    // create a new div with class card and put it into chosenPic
    const cardDiv = document.createElement('cardD');
    cardDiv.className = 'card';
    cardDiv.innerHTML = `<img src="${src}">
                <p class = "text1"><strong>${firstLine}</strong></p>
                <p class = "text1">${secondLine}</p>`;
    chosenPic.innerHTML = '';
    chosenPic.appendChild(cardDiv);

    // add event listener to cardDiv for details, when we do have the details
    if (chosenItem) {
        addItemDetailsPopupToCard(cardDiv, chosenItem);
    }
}


function updateResults(new_data, chosenOrdID) {
    // Load everything into dictionary for faster lookup per ID
    const resultDict = {};
    new_data.result.forEach(function(item) {
        resultDict[item.id] = item;
    });

    let output = '';

    new_data.result.forEach(function(item) {
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
                 <p class="text1"><strong>Similarity: </strong>${similarity}</p>
               </div>`;
    });

    const resultDiv = document.getElementById('result');
    resultDiv.innerHTML = output;
    const resultsDivOverall = document.getElementById('results');
    resultsDivOverall.style.display = "block";

    const divCards = document.querySelectorAll('.card');

    // Open details by clicking on each card
    divCards.forEach(function(cardDiv) {
        const ordId = cardDiv.getAttribute('ord-id');
        const item = resultDict[ordId];
        addItemDetailsPopupToCard(cardDiv, item);
    });
}

function shortenString(str, length) {
    const firstN = str.substring(0, length);
    const lastN = str.substring(str.length - length);
    return `${firstN}...${lastN}`;
}

function addItemDetailsPopupToCard(cardDiv, item) {
    cardDiv.addEventListener('click', function() {
        const popupContainer = document.getElementById('popup-container');
        const popupDetails = document.getElementById('popupDetails');

        const mintedAddressLink = `https://mempool.space/address/${item.minted_address}`;

        // Shortcuts are first four letters, three dots and four last letters
        const short_minted_address = shortenString(item.minted_address, 4);
        const short_ordinals_com_link = shortenString(item.ordinals_com_link, 4);
        const short_tx_id = shortenString(item.tx_id, 4);

        // Take just the first part before space
        const publishedDate = item.datetime.split(' ')[0];

        const content = `
        <div id="popup-content-details">
          <span id="close-btn">&times;</span>
  
          <div class="popup-details">
            <p><strong>ID:</strong> ${item.id}</p>
            <p><strong>Date Published:</strong> ${publishedDate}</p>
            <p><strong>Content type:</strong> ${item.content_type}</p>
            <p><strong>Content length:</strong> ${item.content_length} bytes</p>
            <p><strong>Minted Address:</strong> <a href="${mintedAddressLink}" target="_blank">${short_minted_address}</a></p>
            <p><strong>Ordinals.com link:</strong> <a href="${item.ordinals_com_link}" target="_blank">${short_ordinals_com_link}</a></p>
            <p><strong>Transaction ID:</strong> <a href="${item.mempool_space_link}" target="_blank">${short_tx_id}</a></p>
          </div>
        </div>
      `;

        popupDetails.innerHTML = content;
        popupContainer.style.display = 'flex';

        const closeBtn = document.getElementById('close-btn');
        closeBtn.addEventListener('click', function() {
            popupContainer.style.display = 'none';
        });
    });
}
