var PubNub = require('pubnub')
var http = require('https');


function sendHttp(device, type) {
    /* pubnub test
    var auth_token="109ae5f2-061a-478b-b9ac-b2ac401b1913"
        var st_appid="0a381f5c-6312-4abc-b996-89475f491a83"
        */
    // Wink Connect Service
    var auth_token="9bf8ef2f-b7c6-4395-9578-6d73da9a7a5a"
        var st_appid="824c5fb2-5eda-42f0-bb12-bfde458ba49d"
        var url = "https://graph.api.smartthings.com:443/api/smartapps/installations/" + st_appid + "/update?obj_id="+device+"&obj_type="+type+"&access_token=" + auth_token
        http.get(url, (res) => {
            const statusCode = res.statusCode;
            const contentType = res.headers['content-type'];

            let error;
            if (statusCode !== 200) {
                error = new Error(`Request Failed.\n` +
                        `Status Code: ${statusCode}`);
            } else if (!/^application\/json/.test(contentType)) {
                error = new Error(`Invalid content-type.\n` +
                        `Expected application/json but received ${contentType}`);
            }
            if (error) {
                console.log(error.message);
                // consume response data to free up memory
                res.resume();
                return;
            }

            res.setEncoding('utf8');
            let rawData = '';
            res.on('data', (chunk) => rawData += chunk);
            res.on('end', () => {
                try {
                    let parsedData = JSON.parse(rawData);
                    console.log(parsedData);
                } catch (e) {
                    console.log(e.message);
                }
            });
        }).on('error', (e) => {
            console.log(`Got error: ${e.message}`);
        });
}

function publish() {
   
    pubnub = new PubNub({
        publishKey : 'demo',
        subscribeKey : 'demo'
    })

    winkPubNub = new PubNub({
	subscribeKey : 'sub-c-f7bf7f7e-0542-11e3-a5e8-02ee2ddab7fe',
        ssl: true
    })
       
     /*  
    function publishSampleMessage() {
        console.log("Since we're publishing on subscribe connectEvent, we're sure we'll receive the following publish.");
        var publishConfig = {
            channel : "hello_world",
            message : "Hello from PubNub Docs!"
        }
        pubnub.publish(publishConfig, function(status, response) {
            console.log(status, response);
        })
    }
    pubnub.addListener({
        status: function(statusEvent) {
            if (statusEvent.category === "PNConnectedCategory") {
                publishSampleMessage();
            }
        },
        message: function(message) {
            console.log("New Message!!", message);
        },
        presence: function(presenceEvent) {
            // handle presence
        }
    })      
    console.log("Subscribing..");
    pubnub.subscribe({
        channels: ['hello_world'] 
    });
*/
    function publishWinkMessage() {
        console.log("Since we're publishing on subscribe connectEvent, we're sure we'll receive the following publish.");
        var publishConfig = {
            channel : "b4da8ed9739192268ba5667b4d10545b09e45d83|light_bulb-1702387|user-331666",
            message : "WINK!"
        }
        pubnub.publish(publishConfig, function(status, response) {
            console.log(status, response);
        })
    }
    winkPubNub.addListener({
        status: function(statusEvent) {
            console.log("New status event!!");
            if (statusEvent.category === "PNConnectedCategory") {
                //publishWinkMessage();
            }
        },
        message: function(message) {
            console.log("New Message!!", message);
            //var obj = JSON.parse(message);
            console.log("MSG: ", message.message.device_manufacturer);
            var obj = JSON.parse(message.message);
            console.log("MSG2: ", obj);
            console.log("OBJ_ID", obj.object_id);
            sendHttp(obj.object_id, obj.object_type);
        },
        presence: function(presenceEvent) {
            console.log("New presence event!!");
            // handle presence
        }
    })      
    console.log("Subscribing to Wink channel.");
    winkPubNub.subscribe({
        channels: [ 'b4da8ed9739192268ba5667b4d10545b09e45d83|light_bulb-1702387|user-331666',
                    '842d183c2146ad9758a83921fb7476ed462e440b|light_bulb-2177957|user-331666',
                    '19b834f8cf152a3f2af078db4fa13b432b17f741|remote-85669|user-331666',
                    'b0d4bb20c33f36cefce451504b5b4622e8c03b36|remote-120050|user-331666'] 
        //channels: ['b4da8ed9739192268ba5667b4d10545b09e45d83'] 
    });
};

publish();
