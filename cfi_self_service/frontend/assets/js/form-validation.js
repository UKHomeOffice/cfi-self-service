function validateForm() {

    // Retrieve form fields:
    const fields = {
        firstName: document.getElementById("formFirstName"),
        lastName: document.getElementById("formLastName"),
        emailAddress: document.getElementById("formEmailAddress"),
        teamName: document.getElementById("formTeamName"),
        environmentReq: document.getElementById("formEnvironmentReq")
    };

    // Error messages:
    const errors = {
        firstName: "Please input a first name",
        lastName: "Please input a last name",
        emailAddress: "Please input an email address",
        teamName: "Please input a team name",
        environmentReq: "Please select the environment required"
    };

    // Validate each field:
    let isValid = true;
    for (const fieldName in fields) {
        const field = fields[fieldName];
        const errorElement = document.getElementById(`${fieldName}Error`);
        if (!field || !errorElement) {
            console.error(`Field or error element not found for ${fieldName}`);
            continue;
        }
        if (!field.value.trim()) {
            errorElement.innerHTML = `<i class="bi bi-exclamation-diamond me-1"></i> ${errors[fieldName]}`;
            isValid = false;
        } else {
            errorElement.innerHTML = "";
        }
    }

    return isValid;

}

// Event listener for form submission:
const form = document.querySelector("#new-request-form");
form.addEventListener("submit", function(event) {
    if (!validateForm()) {
        event.preventDefault(); // This prevents form submission if validation fails
    }
});