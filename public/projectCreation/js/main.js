var loginURL = "https://cloud-web-util.ucsd.edu/projectCreation/login.html?redirectURL=https://cloud-web-util.ucsd.edu/projectCreation/createProject.html";
/* Authentication token */
var token;
/* Counter for number of users (this is the number of the next user, so there are num -1 users) */
var num = 2;

/* Runs on page load */
$(document).ready(function(){
  if (typeof(Storage) !== "undefined"){ 
    token = window.localStorage.getItem("loginToken");
    if( !token ){
      window.location.href = loginURL;
    }
  }else{
    var cookies = document.cookie;
    cookies = cookies.split(";");
    var part;
    hasToken = false;
    for(var i = 0; i < cookies.length; i++){
      part = cookies[i];
      if(part.includes("loginToken")){
        token = part.substring(part.indexOf("=") + 1);
        hasToken = true;
      }    
    }
    if(!hasToken){
      window.location.href = loginURL;   
    }
  }
  testToken();
});

/*  Name:         addInput
*   Purpose:      add another text input to the form for another username
*   Description:  Creates a new li with an input and button inside of it and
                  appends it to the ul of usernames
*   Params:       none
*   Return Value: none
*/
function addInput(){
  /* String version of li item to be added */
  var liData = "<li id=\"user"+ num +"\" class=\"list-group-item\"><div><label class=\"col-xs-2 col-form-label custom\">Username</label><div class=\"\"><div class=\"input-group col-lg-10\"><input onclick=\"removeError(\'usernameError\'); removeError(\'duplicateUserError\');\" id=\"user\" name=\"user\" type=\"text\" class=\"form-control\" placeholder=\"user@example.com\"><span class=\"input-group-btn\"><button onclick=\"removeUser(\'user"+ num + "\')\" class=\"btn btn-danger\" type=\"button\"><b>-</b></button></span></div></div></li>"
  var userList = document.getElementById('userList');
  var user = $(liData);
  num++;
  /* Insert the at then end of the ul, but before the errormessage div */
  userList.insertBefore(user[0], document.getElementById("usernameError"));
}

/*  Name:         removeUser
*   Purpose:      remove a text input for another username from the form
*   Description:  Remove the DOM element and subtract 1 from username counter
*   Params:       user - the li that holds the input field
*   Return Value: none
*/
function removeUser(user){
  var userLi = document.getElementById(user);
  userLi.parentElement.removeChild(userLi);
  num--;
}

/*  Name:         realSubmit
*   Purpose:      Make a post of the data from the form
*   Description:  Replaces the standard form submission. Creates a POST request
                  and sends it the url
*   Params:       none
*   Return Value: none
*/
function realSubmit(){
  /* Only post if the form had the correct data in it */
  if(checkForm()){

    removeError("failedCreate");
    removeError("successfulCreate");
    var url = "https://cloud-web-util.ucsd.edu/account";
    var method = "POST";
    var async = true;
    /* accountData is a JSON string of the form data */
    var accountData = createJSON();
    var request = new XMLHttpRequest();
    request.onload = function () {
        var status = request.status; // HTTP response status, e.g., 200 for "200 OK"
        var data = request.responseText; // Returned data, the JSON packet
        if(status == 401){
          data = "Please log in again and try again.";
        }
        if( status >= 500 ){
          data = "Something went wrong on the server";
        }
        if( status == 200){
         showError("successfulCreate");
        }else{
         document.getElementById("failedCreate").innerHTML = "Creation failed: " + data;
         showError("failedCreate");
        }
    }
    request.open(method, url, async);
    request.setRequestHeader('Authorization', token);
    request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    request.send(accountData);

  }
}

/*  Name:         createJSON
*   Purpose:      return the form data formatted as JSON
*   Description:  Creates a plain javascript object and adds fields with string
                  values (values are taken from the form) and then returns
                  the stringified JSON version of this object
*   Params:       none
*   Return Value: string - string version of form data in JSON format
*/
function createJSON(){
  /* Will hold the values from the form */
  var data = Object();
  /* Get all the username input fields */
  var users = document.getElementsByName("user");
  var userNames = new Array();
  /* Fill the array with username values */
  for(var i = 0; i < users.length; i++){
    userNames[i] = users[i].value;
  }
  /* Add the fields and values to this objct */
  data.projectName = document.getElementById("projectName").value;
  data.contactEmail = document.getElementById("contactEmail").value;
  data.contactName = document.getElementById("contactName").value;
  data.users = userNames;
  data.index = document.getElementById("index").value;
  data.isTrial = document.getElementById("trialButton").checked;
  data.warningTime = document.getElementById("warningLength").value;
  data.expirationTime = document.getElementById("trialLength").value; //ALSO TO CHANGE. DEFAULT VALUES

  /* Return JSON string */
  console.log(data);
  return JSON.stringify(data);
}

/*  Name:         checkForm
*   Purpose:      Validate form submission
*   Description:  Checks that all fields are complete and that there are email
                  addresses where applicable
*   Params:       none
*   Return Value: boolean -true if all fields are filled out correctly, otherwise
                  false is returned
*/
function checkForm(){
  /* Return value for this function */
  var submissionIsValid = true;
  /* Get the inputs from the form */
  var projectName = document.getElementById("projectName");
  var contactName = document.getElementById("contactName");
  var contactEmail = document.getElementById("contactEmail");
  var userNames = document.getElementsByName("user");
  var index = document.getElementById("index");
  var warningLength = document.getElementById("warningLength");
  var trialLength = document.getElementById("trialLength");
  var projectType;
  if(document.getElementById("standardButton").checked == true){
    projectType = "Standard";
  }else{
    projectType = "Trial";
  }

  /* Check if any of the fields are blank */
  if(projectName.value == ""){
    showError("projectNameError");
    submissionIsValid = false;
  }

  if(contactName.value == ""){
    showError("contactNameError");
    submissionIsValid = false;
  }

  if(contactEmail.value == ""){
    showError("contactEmailError");
    submissionIsValid = false;
  }

  if(index.value == "" && projectType == "Standard"){
    showError("indexError");
    submissionIsValid = false;
  }

  if(projectType !== "Standard"){
    if(!Number.isInteger(parseInt(trialLength.value))){
      showError("trialLengthError");
      submissionIsValid = false;
    }
    if(!Number.isInteger(parseInt(warningLength.value))){
      showError("warningLengthError");
      submissionIsValid = false;
    }
  }

  for(var i = 0; i < userNames.length; i++){
    if(userNames[i].value == ""){
      showError("usernameError");
      submissionIsValid = false;
    }
  }

  /* Check if fields that are supposed to contain email addresses
     conatin the "@" symbol */
  if(!contactEmail.value.includes("@")){
    showError("contactEmailError");
    submissionIsValid = false;
  }

  for(var i = 0; i < userNames.length; i++){
    if(!userNames[i].value.includes("@")){
      showError("usernameError");
      submissionIsValid = false;
    }
  }

    /* Check for duplicate users */
    if(document.getElementById("usernameError").classList.contains("hidden")){
      for(var i = 0; i < userNames.length; i++){
        for(var j = i + 1; j < userNames.length; j++){
          if( userNames[i].value == userNames[j].value){
            showError("duplicateUserError");
            submissionIsValid = false;
          }
        }
      }
    }

  /* Return whether the form submission was valid */
  return submissionIsValid;
}

/*  Name:         removeError
*   Purpose:      Hides an error message
*   Description:  Adds "hidden" to the class list of the error message div
*   Params:       errorId - the id of the div that needs to be hidden
*   Return Value: none
*/
function removeError(errorId){
  document.getElementById(errorId).classList.add("hidden");
}

/*  Name:         showError
*   Purpose:      Shows an error message
*   Description:  Removes "hidden" from the class list of the error message div
*   Params:       errorId - the id of the div that needs to be shown
*   Return Value: none
*/
function showError(errorId){
  document.getElementById(errorId).classList.remove("hidden");
}

/*  Name:         hideIndex
*   Purpose:      Hides the index input
*   Description:  Adds "hidden" to the class list of the index input and label
*   Params:       none
*   Return Value: none
*/
function hideIndex(){
  document.getElementById("index").classList.add("hidden");
  document.getElementById("index").value = "";
  document.getElementById("indexLabel").classList.add("hidden");

  document.getElementById("trialLength").classList.remove("hidden");
  document.getElementById("trialLength").value = "90";
  document.getElementById("trialLengthLabel").classList.remove("hidden");

  document.getElementById("warningLength").classList.remove("hidden");
  document.getElementById("warningLength").value = "60";
  document.getElementById("warningLengthLabel").classList.remove("hidden");

  removeError("indexError");
}

/*  Name:         showIndex
*   Purpose:      Shows the index input
*   Description:  Removes "hidden" from the class list of the index input and label
*   Params:       none
*   Return Value: none
*/
function showIndex(){
  document.getElementById("index").classList.remove("hidden");
  document.getElementById("indexLabel").classList.remove("hidden");


  document.getElementById("trialLength").classList.add("hidden");
  document.getElementById("trialLength").value = "90";
  document.getElementById("trialLengthLabel").classList.add("hidden");

  document.getElementById("warningLength").classList.add("hidden");
  document.getElementById("warningLength").value = "60";
  document.getElementById("warningLengthLabel").classList.add("hidden");
}

/*  Name:         testToken
*   Purpose:      Test whether the stored token is valid
*   Description:  Sends a get request to requestData with the specified token.
*                 If 401 is return from the reqeust, user if prompted to login again
*   Params:       none
*   Return Value: none
*/
function testToken(){
  var url = "https://cloud-web-util.ucsd.edu/requestData";
  var method = "GET";
  var async = true;
  var request = new XMLHttpRequest();
  request.onload = function () {
      var status = request.status;
      if(status == 401){
        window.location.href = loginURL;
      }
  }
  request.open(method, url, async);
  request.setRequestHeader("Authorization", token);
  request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
  request.send();
}
