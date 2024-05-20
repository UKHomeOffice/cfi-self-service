function validateForm() {

    // Form Fields:
    var isValid = true;
    var emailAddressField = document.getElementById("formEmailAddress");
    var passwordField = document.getElementById("formPassword");

    // Error Tags:
    var emailAddressError = document.getElementById("emailAddressError");
    var passwordError = document.getElementById("passwordError");

    // Validation - Email Address:
    if (emailAddressField.value.trim() === "") {
        emailAddressError.innerHTML = '<i class="bi bi-exclamation-diamond me-1"></i> Please input an email address';
        isValid = false;
    } else {
        emailAddressError.innerHTML = "";
    }

    // Validation - Password:
    if (passwordField.value.trim() === "") {
        passwordError.innerHTML = '<i class="bi bi-exclamation-diamond me-1"></i> Please input a password';
        isValid = false;
    } else {
        passwordError.innerHTML = "";
    }

    // Only return function as true if all fields are completed:
    return isValid;

}