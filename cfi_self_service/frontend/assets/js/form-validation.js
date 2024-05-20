function validateForm() {

    // Retrieve form fields:
    const fields = {
        first_name: document.getElementById("formFirstName"),
        last_name: document.getElementById("formLastName"),
        email_address: document.getElementById("formEmailAddress"),
        team_name: document.getElementById("formTeamName"),
        environment_req: document.getElementById("formEnvironmentReq")
    };

    // Error messages:
    const errors = {
        first_name: "Please input a first name",
        last_name: "Please input a last name",
        email_address: "Please input an email address",
        team_name: "Please input a team name",
        environment_req: "Please select the environment required"
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