document.addEventListener('DOMContentLoaded', function () {
  (function() {
    var pitchLikeForm = document.getElementById('pitchLike');
    if (!pitchLikeForm) {
      console.warn('No pitch like form!');
      return;
    }
    pitchLikeForm.addEventListener('submit', function(e) {
      e.preventDefault();
      var icon = e.target.querySelector('span').querySelector('i');
      var request = new XMLHttpRequest();
      request.onload = function() {
        if (this.status == 200) {
          var response = JSON.parse(request.responseText);
          if (response.liked) {
            icon.className = 'fa fa-heart';
          } else {
            icon.className = 'fa fa-heart-o';
          }
        }
      };
      request.open('POST', this.action);
      request.send(new FormData(this));
    });
  })();
});
