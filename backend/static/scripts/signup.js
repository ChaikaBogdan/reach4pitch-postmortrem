document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('termsAgreed').addEventListener('change', function () {
        document.getElementById('signupButton').disabled = !this.checked;
    });
});
