/* The login page url */
var loginURL = "https://cloud-web-util.ucsd.edu/projectCreation/login.html" 



/*  Name:         GET
*   Purpose:      Send a get request to server
*   Description:  Sends a get request to given url and calls callback with
                  the data
*   Params:       url - the url to send the GET request to
                  callback - the callback functions (should take the data as
                              the parameter)
*   Return Value: none
*/
function GET(url, callback){
  var method = "GET";
  var async = true;
  var request = new XMLHttpRequest();
  request.onload = function(){callback(request)};
  request.open(method, url, async);
  request.setRequestHeader("Authorization", token);
  request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
  request.send();
}

/*  Name:         tokenTestCallback
*   Purpose:      Test token and redirect to login if invalid
*   Description:  Sends a get request and looks at the server response
*   Params:       The data back form the server
*   Return Value: none
*/
function tokenTestCallback(request){
  var status = request.status;
  if(status == 401){
      login(window.location.href);
  }
}

/*  Name:         checkForToken
*   Purpose:      Checks for "loginToken"
*   Description:  Checks for "loginToken" in local storage and then cookies
*   Params:       redirectToLogin - boolean: if true, redirect if the token
                  cannot be found
*   Return Value: true if the token is found and false if the token is not
                  (token may or may not be valid)
*/
function checkForToken(redirectToLogin){
  if (typeof(Storage) !== "undefined"){ 
    token = window.localStorage.getItem("loginToken");
    if( !token ){
      if(redirectToLogin){
        login(window.location.href); 
      }else{
        return false;
      }
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
      if(redirectToLogin){
        window.location.href = loginURL;   
      }else{
        return false;
      }
    }
  }
  return true;
}

/*  Name:         login
*   Purpose:      Redirects to the login page
*   Description:  Redirects to the login page
*   Params:       redirectURL - the value of to be passed as redirectURL in
                                the url
*   Return Value: none
*/
function login(redirectURL){
  window.location.href = loginURL + "?redirectURL=" + redirectURL;
}

/*  Name:         parseURL
*   Purpose:      Get a value from the URL arguments
*   Description:  Parses the url for a value
*   Params:       value - the value to look for
*   Return Value: the value if it exists or an empty string
*/
function parseURL(value){
  var parseVal = window.location.href;

    if(parseVal.includes(value)){
      var index = parseVal.indexOf(value) + value.length + 1; //length of value and the "="
      parseVal = parseVal.substring(index);
      if(parseVal.includes("&")|| parseVal.includes(";") ){
        var index;
        index = parseVal.indexOf(";");
        if(index == -1){
          index = parseVal.indexOf("&");
        }
        parseVal = parseVal.substring(0, index);
      }
      parseVal = decodeURIComponent(parseVal);
      return parseVal;
    }else{
      return "";
    }
}

/*  Name:         showLoadingIcon
*   Purpose:      Display a loading icon and prevent user from clicking
*   Description:  Shows a modal that cannot by unfocussed
*   Params:       name - the name of the modal
*   Return Value: none
*/
function showLoadingIcon(name){
  $('#' + name).modal({
    backdrop: 'static',
    keyboard: false
  }); 
}

/*  Name:         hideLoadingIcon
*   Purpose:      Hides the loading icon 
*   Description:  Toggles the modal
*   Params:       name - the name of the modal
*   Return Value: none
*/
function hideLoadingIcon(name){
  $('#' + name).modal({
    backdrop: 'true',
    keyboard: true
  }); 
  $("#" + name).modal("toggle");
}
