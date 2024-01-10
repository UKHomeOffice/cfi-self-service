function validateForm() {

    // Form Fields:
    var isValid = true;
    var firstNameField = document.getElementById("formFirstName");
    var lastNameField = document.getElementById("formLastName");
    var emailAddressField = document.getElementById("formEmailAddress");
    var teamNameField = document.getElementById("formTeamName");
    var environmentReqField = document.getElementById("formEnvironmentReq");

    // Error Tags:
    var firstNameError = document.getElementById("firstNameError");
    var lastNameError = document.getElementById("lastNameError");
    var emailAddressError = document.getElementById("emailAddressError");
    var teamNameError = document.getElementById("teamNameError");
    var environmentReqError = document.getElementById("environmentReqError");

    // Validation - First Name:
    if (firstNameField.value.trim() === "") {
        firstNameError.innerHTML = '<i class="bi bi-exclamation-diamond me-1"></i> Please input a first name';
        isValid = false;
    } else {
        firstNameError.innerHTML = "";
    }
    // Validation - Last Name:
    if (lastNameField.value.trim() === "") {
        lastNameError.innerHTML = '<i class="bi bi-exclamation-diamond me-1"></i> Please input a last name';
        isValid = false;
    } else {
        lastNameError.innerHTML = "";
    }
    // Validation - Email Address:
    if (emailAddressField.value.trim() === "") {
        emailAddressError.innerHTML = '<i class="bi bi-exclamation-diamond me-1"></i> Please input an email address';
        isValid = false;
    } else {
        emailAddressError.innerHTML = "";
    }
    // Validation - Team:
    if (teamNameField.value.trim() === "") {
        teamNameError.innerHTML = '<i class="bi bi-exclamation-diamond me-1"></i> Please input a team name';
        isValid = false;
    } else {
        teamNameError.innerHTML = "";
    }
    // Validation - Environment:
    if (environmentReqField.value.trim() === "Please select") {
        environmentReqError.innerHTML = '<i class="bi bi-exclamation-diamond me-1"></i> Please select the environment required';
        isValid = false;
    } else {
        environmentReqError.innerHTML = "";
    }

    // Only return function as true if all fields are completed:
    return isValid;

}