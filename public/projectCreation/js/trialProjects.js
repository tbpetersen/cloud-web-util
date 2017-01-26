/* Authentication token */
var token;
/* Counter for number of users (this is the number of the next user, so there are num -1 users) */
var num = 2;
/* Object representing trial projects (may be an empty array) */
var trialProjects;
/* Div with the id of "content-div" */
var mainDiv;
/* The name of the trial that "Upgrade" was clicked for*/
var selectedTrial;

/* Runs on page load */
$(document).ready(function(){
  /* Set up variables */
  mainDiv = document.getElementById("content-div");

  /* Look for the login token in local storage and then in cookies.
     Send the user to the login page if the token does not exist

     Test the login token if it is found. If the token is invalid,
     send the user to the login page.
   */

  /* Check for the login token in local storage */
  checkForToken(true); 
  
  /* Test the token */
  //GET("https://cloud-web-util.ucsd.edu/requestTrials", tokenTestCallback);
  GET("/requestTrials", tokenCallback);
});

/*  Name:         tokenTestCallback
*   Purpose:      the callback function for the response to the GET request
                  with the token
*   Description:  Displays the trials if the token worked or redirects to the
                  login page if 401
*   Params:       the data from the GET request
*   Return Value: none
*  
*   Note: testToken() must be called first to initialize trialProjects
*/
function tokenCallback(request){
      var status = request.status;
      if(status == 401){
        login(window.location.href);
      }else if(status == 500){
        var pa = document.getElementById("text-info");
        pa.innerHTML = "There was an error with the server".bold();
        pa.classList.add("text-danger");
      }
      document.getElementById("loading").style.display = "none";
      trialProjects = JSON.parse(request.responseText);
      populateList();
}

/*  Name:         populateList
*   Purpose:      Display webpage content 
*   Description:  Adds content to the main div based on the data returned from
                  GET request in testToken()
*   Params:       none
*   Return Value: none
*  
*   Note: testToken() must be called first to initialize trialProjects
*/
function populateList(){

  /* Add a panel for each project */
  for(var i = 0; i < trialProjects.length; i++){
    addProjectPanel(trialProjects[i]);
  }

  /* Add a message that there is not data if there is not data */
  if(trialProjects.length == 0 ){  
    var pa = document.getElementById("text-info");
    if(pa.innerHTML == ""){
      pa.innerHTML = "There are currently no trial projects".bold();
      pa.classList.add("text-success");
    }
  }
  
  mainDiv.appendChild(document.createElement("br"));
  
}

/*  Name:         addProjectPanel
*   Purpose:      Adds a single panel to the webpage
*   Description:  Adds panel for projectJSON 
*   Params:       projectJSON - An object with values for "projectName",
                  "contactName" and "contactEmail"
*   Return Value: none
*/
function addProjectPanel(projectJSON){
  var panel = document.createElement("div");
  panel.setAttribute("class", "panel panel-default myPanel");
  panel.setAttribute("id", projectJSON.projectName + "Panel");

  var boldTag = document.createElement("b"); 
  var breakTag = document.createElement("br"); 

  var projectNameP = document.createElement("p"); 
  projectNameP.innerHTML = "Project Name: " + projectJSON.projectName;

  var nameP = document.createElement("p"); 
  nameP.innerHTML = "Contact Name: " + projectJSON.contactName;

  var emailP = document.createElement("p");   
  emailP.innerHTML = "Contact Email: " + projectJSON.contactEmail;
  
  var button = document.createElement("button");
  button.innerHTML = "Upgrade";
  button.setAttribute("class", "btn btn-success");
  button.setAttribute("data-toggle", "modal");
  button.setAttribute("data-target", "#myModal");
  button.onclick = function(){
    document.getElementById("selectedTrialName").innerHTML = projectJSON.projectName;
  };

  boldTag.appendChild(projectNameP);

  panel.appendChild(boldTag);
  panel.appendChild(nameP);
  panel.appendChild(emailP);
  panel.appendChild(button);
  mainDiv.appendChild(panel);
}

/*  Name:         sendPost
*   Purpose:      Upgrades the selected trial to a full project 
*   Description:  Sends a POST to /convertTrialProject 
*   Params:       none
*   Return Value: none
*/
function sendPost(){
var trialName = document.getElementById("selectedTrialName").innerHTML;
selectedTrial = trialName;
var newIndex = document.getElementById("newIndex").value;

if( newIndex == ""){
  $("#noIndexError").css( "display", "block");
  $("#noIndexError").fadeOut(4500);
  return;
}
var url = "https://cloud-web-util.ucsd.edu/convertTrialProject"
	 var method = "POST";
	 var a_sync = true;
	 var request = new XMLHttpRequest();
	 var token = localStorage.getItem("loginToken");
	 request.onload = function () {
	 	 var status = request.status;
	 	 if (status === 401) {
	 	 	window.location.href = "https://cloud-web-util.ucsd.edu/projectCreation/login.html";
	 	 	return;
	 	 }
	 	 if(status !== 200){
	 	 	console.log(request.responseText);
                        document.getElementById("serverErrorMessage").innerHTML = "Error: " + status; 
                        $("#serverError").css( "display", "block");
                        $("#serverError").fadeOut(4500);
                        closeModal();
                        return;
	 	 }
	 	 	
                 closeModal();
                 $("#serverSuccess").css( "display", "block");
                 $("#serverSuccess").fadeOut(4500);
                 var upgraded = document.getElementById(selectedTrial + "Panel");
                 upgraded.parentNode.removeChild(upgraded);
		 console.log(request.responseText);
	 }
	 request.open(method, url, a_sync);
	 request.setRequestHeader('Authorization', token);
	 request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
	 request.send(JSON.stringify([trialName, newIndex]));
}

/*  Name:         closeModal
*   Purpose:      Closes the window for entering index info
*   Description:  Toggles the modal
*   Params:       none
*   Return Value: none
*/
function closeModal(){
  $("#myModal").modal("toggle");
}
