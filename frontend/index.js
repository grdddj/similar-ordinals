const SPONSOR_MINTING_WEBSITE = "https://ordinalswallet.com/inscribe";
const API_ENDPOINT = "https://api.ordsimilarity.com";
// const API_ENDPOINT = "http://localhost:8002";
const RANDOM_RESULTS_ID = "random";

function selectImage() {
    const input = document.getElementById('fileInput');
    input.click();
    input.addEventListener('change', () => {
        const file = input.files[0];
        const fileType = file.type;
        const fileExtension = file.name.split('.').pop().toLowerCase();
        if (fileType.startsWith('image/') || ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg'].includes(fileExtension)) {
            // Showing the chosen picture in a card
            const reader = new FileReader();
            reader.addEventListener('load', (event) => {
                fill_chosen_picture(event.target.result, null);
            });
            reader.readAsDataURL(file);
            // Submitting the image
            submitImage();
        } else {
            alert('Please select an image file.');
        }
    });
}

function submitImage() {
    // If the loading is already shown, not send another request
    const popup = document.getElementById('loadingPopup');
    if (popup.style.display === 'block') {
        return;
    }
    // Show the loading popup
    popup.style.display = "block";

    const input = document.getElementById('fileInput');
    const file = input.files[0];
    const formData = new FormData();
    formData.append('file', file);

    fetch(API_ENDPOINT + '/file', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // Hide the loading popup
            popup.style.display = "none";
            // Get the content hash to show duplicated
            let ordContentHash = null;
            if (data.hasOwnProperty("ord_content_hash")) {
                ordContentHash = data.ord_content_hash;
            }
            // Show the results
            updateResults(data, null, ordContentHash);
            // Showing the trivia funny facts
            showTriviaFooter();
        })
        .catch(error => {
            console.error(error);
            alert("Error when getting data. We apologize, please try later.");
            // Hide the loading popup
            popup.style.display = "none";
        });
}

function fill_chosen_picture(src, chosenItem, possibleTXID) {
    const chosenPic = document.getElementById('chosen-picture');
    let firstLine = '';
    let secondLine = '';
    if (chosenItem === 'mempool') {
        firstLine = 'Mempool ordinal';
        const shortTxID = shortenString(possibleTXID, 4);
        secondLine = `<strong>Tx ID:</strong> <a href="https://mempool.space/tx/${possibleTXID}" target="_blank">${shortTxID}</a>`;
    } else if (chosenItem) {
        firstLine = 'Your ordinal';
        secondLine = chosenItem.id;
    } else {
        firstLine = 'Your Potential Ordinal';
        secondLine = `Mint <a href=${SPONSOR_MINTING_WEBSITE} target="_blank">Here</a>`;
    }

    // create a new div with class card and put it into chosenPic
    const cardDiv = document.createElement('cardD');
    cardDiv.className = 'card';
    cardDiv.innerHTML = `<img src="${src}">
                <p class = "cardText"><strong>${firstLine}</strong></p>
                <p class = "cardText">${secondLine}</p>`;
    chosenPic.innerHTML = '';
    chosenPic.appendChild(cardDiv);

    // add event listener to cardDiv for details, when we do have the details
    if (chosenItem && chosenItem.hasOwnProperty('id')) {
        addItemDetailsPopupToCard(cardDiv, chosenItem);
    }
}

function updateResults(new_data, chosenOrdOrTxID, chosenContentHash) {
    // Load everything into dictionary for faster lookup per ID
    const resultDict = {};
    new_data.result.forEach(function(item) {
        resultDict[item.tx_id] = item;
    });

    let output = '';
    
    new_data.result.forEach(function(item) {
        // Not displaying the item which user chose - by ordID
        // Also, marking those pixel-perfect matches as those
        if (chosenOrdOrTxID && (item.id == chosenOrdOrTxID || item.tx_id == chosenOrdOrTxID)) {
            return;
        }
        let isDuplicate = false;
        if (item.content_hash == chosenContentHash) {
            isDuplicate = true;
        } 

        let similarityScore = (item.similarity / 256 * 100).toFixed(2);
        let redStyleOrNothing = '';
        if (isDuplicate) {
            similarityScore = "DUPLICATE";
            redStyleOrNothing = 'style="background-color: red"';
        } else {
            if (similarityScore === "100.00") {
                similarityScore = "100";
            }
            similarityScore = similarityScore + " %";
        }

        output += `<div class="card" ${redStyleOrNothing} ord-id="${item.id}" tx-id="${item.tx_id}">
                 <img src="${item.hiro_content_link}">
                 <p class="cardText"><strong>Ordinal ID: </strong>${item.id}</p>
                 <p class="cardText"><strong>Similarity: </strong>${similarityScore}</p>
               </div>`;
    });

    const resultDiv = document.getElementById('result');
    resultDiv.innerHTML = output;
    const resultsDivOverall = document.getElementById('results');
    resultsDivOverall.style.display = "block";

    const divCards = document.querySelectorAll('.card');

    // Open details by clicking on each card
    divCards.forEach(function(cardDiv) {
        const txID = cardDiv.getAttribute('tx-id');
        const item = resultDict[txID];
        if (item) {
            addItemDetailsPopupToCard(cardDiv, item);
        }
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
    });
}

function openOrdIdChoicePopup() {
    // Get the custom popup element
    const ordIdInputPopup = document.getElementById("ordIdInputPopup");
    // Display the custom popup
    ordIdInputPopup.style.display = "block";
    // Bringing cursor focus to the input field so user can write immediately
    const ordinalInput = document.getElementById("ordinalInput");
    ordinalInput.focus();
}

function closeOrdIdPopup() {
    // Get the custom popup element
    const ordIdInputPopup = document.getElementById("ordIdInputPopup");
    // Hide the custom popup
    ordIdInputPopup.style.display = "none";
}

function chooseOrdID() {
    // Get the input element
    const ordinalInput = document.getElementById("ordinalInput");
    const inputValue = ordinalInput.value;

    // User cancelled the prompt
    if (inputValue == null) {
        return;
    }
    // User did not enter anything
    if (inputValue == "") {
        return;
    }

    // Check whether it is tx_id or ord_id
    // If its length it 64 or 66, it is tx_id, otherwise ord_id
    if (isTxID(inputValue)) {
        getTxIdResults(inputValue);
    } else if (isOrdID(inputValue)) {
        // User did not enter a valid number
        if (isNaN(inputValue)) {
            alert("Please enter a valid Ordinal ID - a number.");
            return;
        }
        getOrdIdResults(inputValue);
    } else {
        alert("Please enter a valid Ordinal ID or Transaction ID.");
        return;
    }
}

function isTxID(ordIDOrTxID) {
    return ordIDOrTxID.length == 64 || ordIDOrTxID.length == 66;
}

function isOrdID(ordIDOrTxID) {
    return ordIDOrTxID.length < 10;
}


function getTxIdResults(txID) {
    const url = API_ENDPOINT + "/tx_id/" + txID;
    getResultFromURL(url, txID);
}

function getOrdIdResults(ordID) {
    const url = API_ENDPOINT + "/ord_id/" + ordID;
    getResultFromURL(url, ordID);
}

function getResultFromURL(url, ordIDOrTxID) {
    const popup = document.getElementById('loadingPopup');
    // If the loading is already shown, not send another request
    if (popup.style.display === 'block') {
        return;
    }

    // Show the loading popup
    popup.style.display = "block";

    // Close the input
    closeOrdIdPopup();

    fetch(url)
        .then((response) => response.json())
        .then((data) => {
            if (data.result === undefined) {
                alert("SVG pictures are not supported. We apologize. Please check input and try it again.");
                // Hide the loading popup
                popup.style.display = "none";
                // Open the input again so user can correct it
                openOrdIdChoicePopup();
                return;
            }
            if (data.result.length == 0) {
                alert("Given Ordinal ID is not a valid picture.");
                // Hide the loading popup
                popup.style.display = "none";
                // Open the input again so user can correct it
                openOrdIdChoicePopup();
                return;
            }
            // Possibly we have chosen a random ordID, so need to check which we actually got
            if (ordIDOrTxID === RANDOM_RESULTS_ID && data.hasOwnProperty("ord_id")) {
                ordIDOrTxID = data.ord_id;
            }

            // Show the chosen picture if we find it in the list (show mempool picture if it is mempool)
            let chosenContentHash = null;
            if (data.mempool) {
                chosenContentHash = data.ord_content_hash;
                fill_chosen_picture(data.chosen_content_link, "mempool", ordIDOrTxID);
            } else {
                const chosenItem = data.result.find((item) => (item.id == ordIDOrTxID || item.tx_id == ordIDOrTxID));
                if (chosenItem) {
                    fill_chosen_picture(chosenItem.hiro_content_link, chosenItem);
                    chosenContentHash = chosenItem.content_hash;
                }
            }

            // Show the results
            updateResults(data, ordIDOrTxID, chosenContentHash);
            // Clear the input
            const ordinalInput = document.getElementById("ordinalInput");
            ordinalInput.value = "";
            // Update the URL to contain ord_id=ordID parameter
            if (ordIDOrTxID.length > 10) {
                updateURLWithQueryParamAndDeleteAllOthers("tx_id", ordIDOrTxID);
            } else {
                updateURLWithQueryParamAndDeleteAllOthers("ord_id", ordIDOrTxID);
            }
            // Showing the trivia funny facts
            showTriviaFooter();
            // Scrolling the view to see the beginning of results
            const chosenPicture = document.getElementById('chosen-picture');
            chosenPicture.scrollIntoView({ behavior: 'smooth' });
            // Hide the loading popup
            popup.style.display = "none";
        })
        .catch((error) => {
            console.error(error);
            alert(
                "Error when getting data. We apologize, please try later."
            );
            // Close the input popup
            closeOrdIdPopup();
            // Hide the loading popup
            popup.style.display = "none";
        });
}

function showTriviaFooter() {
    const triviaFooter = document.getElementById("trivia");
    triviaFooter.style.display = "block";
}

function updateURLWithQueryParamAndDeleteAllOthers(name, value) {
    const url = new URL(window.location.href);
    // Clear all existing query parameters
    url.search = '';
    url.searchParams.set(name, value);
    window.history.pushState({}, "", url);
}

function getRandomResults() {
    getOrdIdResults(RANDOM_RESULTS_ID);
}

window.addEventListener("click", function(event) {
    const ordIdInputPopup = document.getElementById("ordIdInputPopup");
    if (event.target == ordIdInputPopup) {
        closeOrdIdPopup();
    }
});

// Keyboard shortcuts
document.addEventListener("keydown", function(event) {
    // Pressing C key (CHOOSE) will trigger the ordID input
    if (event.key === "c") {
        openOrdIdChoicePopup();
        event.preventDefault();
        return;
    }
    // Pressing U (UPLOAD) key will trigger the upload input
    if (event.key === "u") {
        selectImage();
        event.preventDefault();
        return;
    }
    // Pressing F (FEELING) key will get random results
    if (event.key === "f") {
        getRandomResults();
        event.preventDefault();
        return;
    }
    // Pressing Esc will go away from the popup
    if (event.key === "Escape") {
        const popupContainer = document.getElementById("popup-container");
        const ordIdInputPopup = document.getElementById("ordIdInputPopup");
        if (popupContainer.style.display !== 'none') {
            popupContainer.style.display = 'none';
            event.preventDefault();
            return;
        } else if (ordIdInputPopup.style.display !== 'none') {
            ordIdInputPopup.style.display = 'none';
            event.preventDefault();
            return;
        }
    }
    // Pressing enter will submit the form when focus is on the input
    if (event.key === "Enter") {
        const ordinalInput = document.getElementById("ordinalInput");
        if (document.activeElement === ordinalInput) {
            event.preventDefault();
            chooseOrdID();
        }
    }
});

// Look at the URL parameters and possibly do some actions
window.onload = function() {
    const queryParams = new URLSearchParams(window.location.search);
    // Get results from ord_id=XXX
    const ordID = queryParams.get('ord_id');
    if (ordID) {
        getOrdIdResults(ordID);
        return;
    }
    // Get results from tx_id=XXX
    const txID = queryParams.get('tx_id');
    if (txID) {
        getTxIdResults(txID);
        return;
    }
};
