/* Token used for logging in */
var token;

/* The default page that the user will be directed to after logging in */
var redirectURL = "https://cloud-web-util.ucsd.edu/projectCreation/createProject.html";


/* Load once the page finishes loading */
$(document).ready(function(){
  /* Update redirectURL to represent the page that the user should be
     directed to (if another page was specified at all) */
  getRedirect();  
  if(checkForToken(false)){
    GET("/requestTrials", loginTestCallback);
  }else{
    document.getElementById("content-div").style.display = "block";
    document.getElementById("loading").style.display = "none";
  }
});

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
    getLoginToken();
  } 
  return false;
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
  if(document.getElementById("username").value == "" || document.getElementById("pass").value == ""){
    showError("formError");
    return false;
  }else{
    return true;
  }
}

/*  Name:         getLoginToken
*   Purpose:      Get a token used to make requests and store it in localStorage
*   Description:  Sends a get request and gets a token as the response text
*   Params:       none
*   Return Value: none
*/
function getLoginToken(){

  var username = document.getElementById("username").value;
  username = username.toLowerCase();
  if(username.indexOf('@ucsd.edu') !== -1)
    username = username.replace("@ucsd.edu", "@sdsc.edu");
  if(username.indexOf('@sdsc.edu') === -1)
    username = username + "@sdsc.edu";

  var url = "https://cloud-web-util.ucsd.edu/login";
  var method = "GET";
  var async = true;
  var request = new XMLHttpRequest();
  request.onload = function () {
      var status = request.status;
      if(status == 401){
        showError("authError");
        return;
      }else if(status >= 500){
        showError("backendError");
        return;
      }else{
        token = request.responseText; // Returned sessionID
        storeToken();
        window.location.href = redirectURL;
      }
  }
  request.open(method, url, async);
  request.setRequestHeader('Authorization', btoa(username + ":" + document.getElementById("pass").value));
  request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
  request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
  request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
  request.setRequestHeader("Pragma", "no-cache");
  //request.setRequestHeader("Cache-Control", "no-cache, no-store, must-revalidate");
  //request.setRequestHeader("Expires", "0");
  request.send();
}

/*  Name:         removeError
*   Purpose:      Hides an error message
*   Description:  Adds "hidden" to the class list of the error message div
*   Params:       errorId - the id of the div that needs to be hidden
*   Return Value: none
*/
function removeError(errorId){
  document.getElementById(errorId).classList.add("hidden");
  document.getElementById(errorId).style.display = "none";
}

/*  Name:         showError
*   Purpose:      Shows an error message
*   Description:  Removes "hidden" from the class list of the error message div
*   Params:       errorId - the id of the div that needs to be shown
*   Return Value: none
*/
function showError(errorId){
  document.getElementById(errorId).classList.remove("hidden");
  document.getElementById(errorId).style.display = "block";
}

/*  Name:         storeToken
*   Purpose:      Store the auth token
*   Description:  Store the auth token in local storage or as a cookie.
                  Regardless of method, it is named "loginToken".
*   Params:       none
*   Return Value: none
*/
function storeToken(){
  if (typeof(Storage) !== "undefined") {
    window.localStorage.setItem("loginToken", token);
  }else{
    document.cookie = "loginToken=" + token;
  }
}

/*  Name:         getRedirect
*   Purpose:      Update the url of page to redirect to
*   Description:  Search the url parameters for the variable "redirectURL" and
                  update accordingly. Do notihng if there is no redirectURL 
                  (default redirect is to the createProjectPage) 
*   Params:       none
*   Return Value: none
*/
function getRedirect(){
  var url = window.location.href;
  if(url.includes("redirectURL")){
    var index= url.indexOf("redirectURL") + 12; // "redirectURL" is 12 characters long
    url = url.substring(index);
    if(url.includes("&")|| url.includes(";") ){
      var index;
      index = url.indexOf(";");
      if(index == -1){
        index = url.indexOf("&");
      }
      url =  url.substring(0, index);
    } 
    redirectURL = url;
  }
}

function loginTestCallback(data){
  if(data.status == 200){
    window.location.href = "/projectCreation/createProject.html";
  }else{
    document.getElementById("content-div").style.display = "block";
    document.getElementById("loading").style.display = "none";
  }
}
