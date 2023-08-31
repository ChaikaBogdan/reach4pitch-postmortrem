document.addEventListener('DOMContentLoaded', function() {
  function openModal(el) {
    el.classList.add('is-active');
  }

  function closeModal(el) {
    el.classList.remove('is-active');
  }

  function closeAllModals() {
    document.querySelectorAll('.modal').forEach(closeModal);
  }

  function openModalByTrigger(trigger) {
    var targetId = trigger.dataset.target;
    var target = document.getElementById(targetId);
    if (target) {
      trigger.addEventListener('click', function() {
        openModal(target);
      });
    } else {
      console.error('Trigger target not found - ' + targetId);
    }
  }

  function closeModalByTrigger(trigger) {
    var target = trigger.closest('.modal');
    trigger.addEventListener('click', function() {
      closeModal(target);
    });
  }

  document.querySelectorAll('.js-modal-trigger').forEach(openModalByTrigger);

  // Add a click event on various child elements to close the parent modal
  document.querySelectorAll(
    '.modal-background, .modal-close, .modal-card-head .delete, .modal-card-foot .button'
  ).forEach(closeModalByTrigger);


  // Add a keyboard event to close all modals
  document.addEventListener('keydown', function(event) {
    var e = event || window.event;

    if (e.keyCode === 27) { // Escape key
      closeAllModals();
    }
  });
});
