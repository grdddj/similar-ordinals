document.addEventListener('DOMContentLoaded', function() {
  const resultDiv = document.getElementById('result');
  const result = JSON.parse(localStorage.getItem('resultData'));

  let output = '';

  result.result.forEach(function(item) {
    output += `<div class="card">
                 <img src="${item.hiro_content_link}">
                 <button class="id-btn" data-id="${item.id}" data-img="${item.hiro_content_link}" data-date="${item.datetime}" data-address="${item.minted_address}" data-link="${item.ordinals_com_link}" data-txid="${item.tx_id}">Ordinal ID: ${item.id}</button>
               </div>`;
  });

  resultDiv.innerHTML = output;

  const idBtns = document.querySelectorAll('.id-btn');
  const popupContainer = document.getElementById('popup-container');
  const popup = document.getElementById('popup');

  idBtns.forEach(function(btn) {
    btn.addEventListener('click', function() {
      const id = btn.getAttribute('data-id');
      const img = btn.getAttribute('data-img');
      const date = btn.getAttribute('data-date');
      const address = btn.getAttribute('data-address');
      const link = btn.getAttribute('data-link');
      const txid = btn.getAttribute('data-txid');

      const content = `
        <div class="popup-content">
          <span id="close-btn">&times;</span>
          
         
          <div class="popup-details">
            <p><strong>ID:</strong> ${id}</p>
            <p><strong>Time Published:</strong> ${date}</p>
            <p><strong>Minted Address:</strong> ${address}</p>
            <p><strong>Ordinals Link:</strong> ${link}</p>
            <p><strong>Transaction ID:</strong> ${txid}</p>
          </div>
        </div>
      `;

      popup.innerHTML = content;
      popupContainer.style.display = 'flex';

      const closeBtn = document.getElementById('close-btn');
      closeBtn.addEventListener('click', function() {
        popupContainer.style.display = 'none';
      });
    });
  });
});
