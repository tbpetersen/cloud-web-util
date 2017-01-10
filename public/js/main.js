$(document).ready(function () {

	$('.star').on('click', function () {
      $(this).toggleClass('star-checked');
    });

    $('.ckbox label').on('click', function () {
      $(this).parents('tr').toggleClass('selected');
    });

    $('.btn-filter').on('click', function () {
      var $target = $(this).data('target');
      if ($target != 'all') {
        $('.table tr').css('display', 'none');
        $('.table tr[data-status="' + $target + '"]').fadeIn('slow');
      } else {
        $('.table tr').css('display', 'none').fadeIn('slow');
      }
    });

 });

  // Counter number of valid projects
  var valCount = 0;

   function getNote(name,x) {
 	document.getElementById(name+'-count').innerHTML = x;
 }

 function load() {
	 // getToken();
	 var url = "https://cloud-web-util.ucsd.edu/requestData"
	 var method = "GET";
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
	 	 }
	 	 	
		 var data = JSON.parse(request.responseText);
		 processValidData(data);
		 processWeirdData(data);
	 }
	 request.open(method, url, a_sync);
	 request.setRequestHeader('Authorization', token);
	 request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
	 request.send();
 }
 function canEmailAgain(data){
 	if(data.length === 0)
 		return true;

 	var max = Math.max.apply(null, data);
 	max = moment.unix(max).toDate();//.getTime();
 	var threshold = new Date()
 	threshold.setDate(max.getDate() + 30);

 	return new Date() >= threshold;

 }

 var my_data;
 function processValidData(data) {
	 valid = data.validProjects;
	 my_data = valid;
	 var count = Object.keys(valid).length;
	 getNote("valid",count);

	 $.each(valid, function(index) { //loop through each project
		 var items = [];
		 items.push("<tr>");
		 // Create Email Button
		 if(canEmailAgain(valid[index].emailDates))
		 	items.push("<td align='center'><a class='btn btn-default email'><em class='fa fa-paper-plane-o'></em></a></td>");
		 else
		 	items.push("<td align='center'><a disabled class='btn btn-default email'><em class='fa fa-paper-plane-o'></em></a></td>");

		 // Add Dates
		 items.push("<td>")
		 for(i=0; i < valid[index].emailDates.length; i++) {
			 var unix = valid[index].emailDates[i];
			 var timestamp = moment.unix(unix);
			 var dates = timestamp.format("MM-DD-YYYY");
			 items.push(dates);
		 }
		 items.push("</td>");

		 // Add the Status of Project
		 items.push("<td>");
		 items.push(valid[index].warningLevel);
		 items.push("</td>")

		 // Add Ticket Numbers
		 items.push("<td>");
		 for(i=0; i < valid[index].ticketNumbers.length; i++) {
		 	var nums = valid[index].ticketNumbers[i].toString()+"\n";
		 	items.push("<a href=\"https://footprints.sdsc.edu/MRcgi/MRlogin.pl?DL=");
		 	items.push(nums.toString());
		 	items.push("DA3\">");
		 	items.push(nums);
		 	items.push("</a>")
		 }
		 items.push("</td>");

		 // Add Emails
		 if (valid[index].contactEmail != null) {
		 	items.push("<td>");
		 	for(i=0; i < valid[index].contactEmail.length; i++) {
			 	var emails = valid[index].contactEmail[i].toString()+"\n";
			 	items.push(emails);
		 	}
		 	items.push("</td>");
		 }


		 //Add Name
		 items.push("<td class='name'>");
		 items.push(valid[index].projectName);
		 items.push("</td>");

		 //Add Types
		 items.push("<td>");
		 for(i=0; i < valid[index].failingType.length; i++) {
			 var types = valid[index].failingType[i].toString()+"\n";
			 items.push(types);
		 }
		 items.push("</td>");

		 items.push("</tr>");
		 var row = items.join("");
		 $('#valid').append(row);
	 });
 }


 function processWeirdData(data) {
	 weird = data.weirdTickets;
	 //var count = Object.keys(weird).length;
	 //getNote("weird",count);
	 $.each(weird, function(index) { //loop through each project
		 var items = [];
		 items.push("<tr>");
		 // Add ticket Numbers
		 items.push("<td>");

		 var nums = weird[index].ticketNumber.toString();
		 items.push("<a href=\"https://footprints.sdsc.edu/MRcgi/MRlogin.pl?DL=");
		 items.push(nums.toString());
		 items.push("DA3\">");
		 items.push(nums);
		 items.push("</a>");
		 items.push("</td>");

		 //Add Name
		 items.push("<td class='name'>");
		 items.push(weird[index].projectName);
		 items.push("</td>");

		 //Add Month
		 items.push("<td>");
		 items.push(weird[index].month.toString());
		 items.push("</td>");

		 //Add Types
		 items.push("<td>");
		 items.push(weird[index].failingType);
		 items.push("</td>");

		 items.push("</tr>");
		 var row = items.join("");
		 $('#weird').append(row);

	 });
 }

/****
	Loads Valid Project Data into Tables
****/
 function loadValidData() {
	 $.getJSON( "data.json", function(data) {
		 processValidData(data);
	 });
 }


 /****
 	Loads Weird Tickets into Tables
 ****/
 function loadWeirdData() {
	 $.getJSON( "data.json", function(data) {
		 processWeirdData(data);
	 });
 }

 function getToken(){
	 var url = "https://cloud-web-util.ucsd.edu/login";
	 var method = "GET";
	 var a_sync = true;
	 var request = new XMLHttpRequest();
 	 request.onload = function () {
 		  var status = request.status;
			if (status == 401) {
				window.location.href = "https://www.cloud-web-util.ucsd.edu/ProjectCreation/login.html";
				return;
			}
 		   var id = request.responseText;
		   localStorage.setItem("token",id);
 	 }
	 request.open(method, url, a_sync);
	 request.setRequestHeader('Authorization', window.btoa("test" +":"+"test"));
	 request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
	 request.send();


 }



$(document).on("click",".email" ,function() {
	var $item = $(this).closest("tr").find(".name").text();
	console.log($(this).parent());
	var url = "https://cloud-web-util.ucsd.edu/" + $item;
	var method = "POST";
	var a_sync = true;
	var request = new XMLHttpRequest();
	var token = localStorage.getItem("loginToken");
	request.onload = function () {
		var status = request.status;
		if (status != 200) {
			$.notifyBar({
        		cssClass: "error",
        		html: "Error occurred! Email not sent"
    		});
		}
		else {
			$.notifyBar({
        		cssClass: "success",
        		html: "Email has been sent "
    		});
    		$(this).closest("tr").hide();

		}
		var data = request.responseText;
	}
	request.open(method, url, a_sync);
	request.setRequestHeader('Authorization', token);
	request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
	request.send();
});
