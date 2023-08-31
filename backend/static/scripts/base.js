document.addEventListener('DOMContentLoaded', function() {
  function expandBurger(trigger) {
    var targetId = trigger.dataset.target;
    var target = document.getElementById(targetId);
    if (target) {
      trigger.addEventListener('click', function () {
        trigger.classList.toggle('is-active');
        target.classList.toggle('is-active');
      });
    } else {
      console.error('Trigger target not found - ' + targetId);
    }
  }
  document.querySelectorAll('.navbar-burger').forEach(expandBurger);

  var notificationCount = document.querySelector('#notification-dropdown .notification-badge');

  function hideNotification(trigger) {
    var notification = trigger.closest('.notification');
    trigger.addEventListener('submit', function (e) {
      e.preventDefault();
      var request = new XMLHttpRequest();
      request.onload = function () {
        if (this.status == 200) {
          notification.parentNode.removeChild(notification);
          notificationCount.textContent = (
            parseInt(notificationCount.textContent.trim()) - 1
          ).toString();
        }
      };
      request.open('POST', this.action);
      request.send(new FormData(this));
    });
  }
  document.querySelectorAll('.notification .hide').forEach(hideNotification);

  function deleteNotification(trigger) {
    const notification = trigger.parentNode;
    if (notification.classList.contains('hide')) {
      return;
    }
    trigger.addEventListener('click', function () {
      notification.parentNode.removeChild(notification);
    });
  }
  document.querySelectorAll('.notification .delete').forEach(deleteNotification);
});
