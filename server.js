//https://github.com/brianc/node-postgres
var http = require("https");
var fs = require('fs');
var atob = require('atob');
var path = require('path');
var fs = require('fs');
var crypto = require('crypto');
var spawn = require("child_process").spawn;

var port = 443;
const ALLOWED_USERNAMES = ['ranakashima@sdsc.edu', 'kcoakley@sdsc.edu', 'colby@sdsc.edu', 'c1mckay@sdsc.edu', 'dferbert@sdsc.edu', 'tbpetersen@sdsc.edu'];
//const ALLOWED_USERNAMES = ['ranakashima@sdsc.edu', 'kcoakley@sdsc.edu', 'colby@sdsc.edu', 'c1mckay@sdsc.edu', 'dferbert@sdsc.edu'];
const python_cmd = 'python';

var options = {
  key : fs.readFileSync('cloud-web-util.key'),
  cert: fs.readFileSync('cloud-web-util.crt')
};


var server = http.createServer(options, function(request, response){
	if(request.method === 'GET'){
		if(request.url === '/requestData'){
			if(badToken(request)){
				sendUnauthorized(response);
				return;
			}
			getData(response);
			return;
		}else if(request.url === '/login'){
			var auth = request.headers.authorization;			
			
			authenticate(auth, response)
			.then((okay_username) => {
				if(okay_username){
					response.statusCode = 200;
					response.end(getKey(okay_username));
				}else{
					sendUnauthorized(response);
				}
			});
		
			return;
		}else if(request.url === '/requestTrials'){
			if(badToken(request)){
				sendUnauthorized(response);
				return;
			}
			sendTrialAccountData(response);

			return
		}else{
			serveFile(request, response);
			return;
		}
	}else if(request.method === 'POST'){
		Promise.all([Promise.resolve(badToken(request, response)), authenticate(request.headers.authorization)])
			.then((results) => {
				var hasGoodToken = !results[0];
				var goodCredentials = results[1];
				var username = goodCredentials;
				if(goodCredentials || hasGoodToken){
					if(request.url === '/account'){
						extractHTTPData(request)
						.then((data) => {
							createAccount(response, data);
						});
					}else if(request.url === '/holonetQuery'){
						queryHolonet(request, response);
						return;
					}else if(request.url === '/trelloCompliment'){
						getTrelloData(request, response);
						return;
					}else if(request.url === '/trelloLogin'){
						runTrelloLogin(request, response);
						return;
					}else{
						var superUserCredential = username && ALLOWED_USERNAMES.indexOf(username.toLowerCase()) !== -1;
						var superUserToken = currentUser && ALLOWED_USERNAMES.indexOf(currentUser.toLowerCase()) !== -1;
						if(!superUserToken && !superUserCredential){
							sendUnauthorized(response);
							return;
						}
						if(request.url === '/new-commvault-ticket'){
							newCommvaultTicket(request, response);
						}else if(request.url === '/convertTrialProject'){
							convertTrialProject(request, response);
						}else{			
							sendEmail(request.url.substring(1), response);	
						}
					}
				}else{
					sendUnauthorized(response);
				}
			}).catch((err) => {
				response.statusCode = 500;
				response.end(err.toString());
				console.log(err.toString());
			});
		
		return;
	}else{
		sendUnauthorized(response);
	}
});

var pf = require('portfinder');
pf.basePort = port;
pf.getPort(function(err, pt){
	if(err){
		console.log(err);
		return;
	}

});


server.listen(port);


function extractHTTPData(request){
	return new Promise((resolve, reject) => {
		var body = [];
		request.on('data', function(chunk) {
		  body.push(chunk);
		}).on('end', function() {
		  body = Buffer.concat(body).toString();
		  resolve(body);
		});
	});
}

function serveFile(request, response){
	var filePath = '/var/www/public/';
	if(request.url === '/'){
		filePath += 'index.html';
	}else{
		filePath += request.url.substring(1);
	}
	var questionIndex = filePath.indexOf("?");
	if(questionIndex !== -1)
		filePath = filePath.substring(0, questionIndex);

    var extname = path.extname(filePath);
    var contentType = 'text/html';
    switch (extname) {
        case '.js':
            contentType = 'text/javascript';
            break;
        case '.css':
            contentType = 'text/css';
            break;
        case '.json':
            contentType = 'application/json';
            break;
        case '.png':
            contentType = 'image/png';
            break;      
        case '.jpg':
            contentType = 'image/jpg';
            break;
        case '.wav':
            contentType = 'audio/wav';
            break;
    }

    fs.readFile(filePath, function(error, content) {
        if (error) {
            if(error.code == 'ENOENT'){
                fs.readFile('./404.html', function(error, content) {
                    response.writeHead(200, { 'Content-Type': contentType });
                    response.end(content, 'utf-8');
                });
            }
            else {
            	console.log(error);
                response.writeHead(500);
                response.end('Sorry, check with the site admin for error: '+error.code+' ..\n');
                response.end(); 
            }
        }
        else {
            response.writeHead(200, { 'Content-Type': contentType });
            response.end(content, 'utf-8');
        }
    });
}

function newCommvaultTicket(request, response){
	extractHTTPData(request)
	.then((data) => {
		runPythonScript(response, 'createCommvaultTicket.py', [data]);
	});
}

function sendTrialAccountData(response){
	runPythonScript(response, 'trialAccountData.py', []);
}

function runTrelloLogin(request, response){
	extractHTTPData(request)
	.then((data) => {
		if(data)
			data = [data];
		runPythonScript(response, 'pyfootprints/trelloLogin.py', data);
	});
}

function getTrelloData(request, response){
	extractHTTPData(request)
	.then((data) => {
		runPythonScript(response, 'pyfootprints/assignedTickets.py', [data])
	});
}

function queryHolonet(request, response){
	extractHTTPData(request)
	.then((data) => {
		runPythonScript(response, 'holonetComm.py', [data]);
	});
}

function convertTrialProject(request, response){
	extractHTTPData(request)
	.then((data) => {
		runPythonScript(response, 'trialToPaidCloudProject.py', [data]);
	});
}

function getData(response){
	runPythonScript(response, 'extractor.py', ['GET']);
}

function sendEmail(email, response){
	runPythonScript(response, 'extractor.py', ['POST', email]);
}

function createAccount(response, data){
	runPythonScript(response, 'extractor.py', ['ACCOUNT', data]);
}

function runPythonScript(response, fileName, args){
	args.unshift(fileName);
	var py = spawn(python_cmd, args);
	var dataString = '';
	var erString = '';
	var sent = false;

	py.on('error', function(err){
		response.statusCode = 400;
		response.end("{'error':\'" + err.toString() + "\'}");
		sent = true;
	});

	py.stdout.on('data', function(data){
	  	dataString += data.toString();
	});
	py.stderr.on('data', function(data){
	  erString += data.toString();
	});

	py.stdout.on('end', function(){
		if(sent)
			return;
		if(erString.length > 0){
			console.log(erString);
			if(erString.indexOf('EmailSpamError') > -1){
				response.statusCode = 405;
				response.end("EmailSpam");
			}
			else if(erString.indexOf('BillingQueryError') > -1){
				response.statusCode = 405;
				response.end("BillingQueryError");
			}
			else if(erString.indexOf('NoProjectError') > -1){
				response.statusCode = 405;
				response.end("NoProject");
			}else if(erString.indexOf('ProjectNameTaken') > -1){
				response.statusCode = 405;
				response.end("ProjectNameTaken");
			}else if(erString.indexOf('InvalidCharacters') > -1){
				response.statusCode = 405;
				response.end("InvalidProjectName");
			}else{
				console.log(erString);
				response.statusCode = 500;
				response.end(erString);
			}
		}else{
			response.statusCode = 200;
			response.end(dataString);			
		}
	});
	py.stdin.end();
}

function authenticate(auth){


	return new Promise((resolve, reject) => {

		var sent = false;
		var sendInvalid = function(){
			if(sent)
				return;
			sent = true;
			resolve(false);
		}
		
		try{
			auth = atob(auth).split(':');
		}catch(err){
			sendInvalid();
			return;
		}
		var username = auth[0], password = auth[1];

		
		var py = spawn(python_cmd, ['authenticator.py', username, password]);

		py.on('error', function(err){
			sendInvalid();
		});
		py.stderr.on('data', function(data){
			sendInvalid();
		});

		py.stdout.on('end', function(){
			if(sent)
				return;
			else
				resolve(username);
		});
		py.stdin.end();
	});
	
}

var currentKey = null;
var currentUser = null;

function getKey(user){
	var len = 128;
	currentKey = crypto.randomBytes(Math.ceil(len/2))
        .toString('hex') // convert to hexadecimal format
        .slice(0,len); //slice ignores how long it actually is. no erros thrown
    currentUser = user;
    return currentKey;
}

function badToken(request){
	if(!currentKey || request.headers.authorization !== currentKey){
		return true;
	}
	return false;
}

function goodToken(request){
	return !badToken(request);
}

function sendUnauthorized(response){
	response.statusCode = 401;
	response.end();
}